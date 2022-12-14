"""Payload-Range diagram computation."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.


from importlib.resources import path

import numpy as np
import openmdao.api as om
from pyDOE2 import lhs
from scipy.interpolate import interp1d

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem
from fastoad.openmdao.problem import get_variable_list_from_system
from . import resources
from .mission_run import MissionRun
from .mission_wrapper import MissionWrapper
from ..mission_definition.schema import MissionDefinition


@RegisterOpenMDAOSystem("fastoad.performances.payload_range", domain=ModelDomain.PERFORMANCE)
class PayloadRange(om.Group):
    """OpenMDAO component for computing data for payload-range plots."""

    def initialize(self):
        self.options.declare(
            "propulsion_id",
            default="",
            types=str,
            desc="(mandatory) The identifier of the propulsion wrapper.",
        )
        self.options.declare(
            "mission_file_path",
            default="::sizing_mission",
            types=(str, MissionDefinition),
            allow_none=True,
            desc="The path to file that defines the mission.\n"
            'If can also begin with two colons "::" to use pre-defined missions:\n'
            '  - "::sizing_mission" : design mission for CeRAS-01\n'
            '  - "::breguet" : a simple mission with Breguet formula for cruise, and input\n'
            "    coefficients for fuel reserve and fuel consumption during climb and descent",
        )
        self.options.declare(
            "mission_name",
            default=None,
            types=str,
            allow_none=True,
            desc="The mission name. Required if mission file defines several missions.",
        )
        self.options.declare(
            "reference_area_variable",
            default="data:geometry:wing:area",
            types=str,
            desc="Defines the name of the variable for providing aircraft reference surface area.",
        )
        self.options.declare(
            "nb_contour_points",
            default=4,
            types=int,
            lower=4,
            desc='If >4, additional points are used in the final "MFW slope" of '
            "the diagram contour.",
        )
        self.options.declare(
            "nb_grid_points",
            default=0,
            types=int,
            lower=0,
            desc="If >0, the provided number of points inside the payload-range "
            "contour will be computed.",
        )
        self.options.declare(
            "grid_random_seed",
            default=None,
            types=int,
            allow_none=True,
            desc="Used as random state for initializing the Latin Hypercube Sampling "
            "algorithm for generating the inner grid.",
        )
        self.options.declare(
            "min_payload_ratio",
            default=0.3,
            lower=0.0,
            upper=0.9,
            desc="Sets the minimum payload for inner grid points, as a ratio w.r.t. max payload.",
        )
        self.options.declare(
            "min_block_fuel_ratio",
            default=0.3,
            lower=0.0,
            upper=0.9,
            desc="Sets the minimum block fuel for inner grid points, as a ratio w.r.t. max "
            "possible fuel weight for the current payload.",
        )

    def setup(self):

        if "::" in self.options["mission_file_path"]:
            # The configuration file parser will have added the working directory before
            # the file name. But as the user-provided string begins with "::", we just
            # have to ignore all before "::".
            i = self.options["mission_file_path"].index("::")
            file_name = self.options["mission_file_path"][i + 2 :] + ".yml"
            with path(resources, file_name) as mission_input_file:
                self.options["mission_file_path"] = MissionDefinition(mission_input_file)

        self._add_payload_range_contour_group()
        if self.options["nb_grid_points"] > 0:
            self._add_payload_range_grid_group()

    def _add_payload_range_contour_group(self):
        """Creates a group for computing payload-range contour."""
        mission_name = self.options["mission_name"]
        nb_contour_points = self.options["nb_contour_points"]

        group = om.Group()

        group.add_subsystem(
            "input_values",
            PayloadRangeContourInputValues(mission_name=mission_name, nb_points=nb_contour_points),
            promotes=["*"],
        )

        var_connections = [
            (
                f"data:payload_range:{mission_name}:block_fuel",
                f"data:mission:{mission_name}:block_fuel",
            ),
            (
                f"data:payload_range:{mission_name}:TOW",
                f"data:mission:{mission_name}:TOW",
            ),
        ]

        mission_wrapper = MissionWrapper(
            self.options["mission_file_path"],
            mission_name=mission_name,
            force_all_block_fuel_usage=True,
        )

        self._add_mission_runs(group, mission_wrapper, nb_contour_points, var_connections)

        mux_comp = group.add_subsystem(name="mux", subsys=om.MuxComp(vec_size=nb_contour_points))
        mux_comp.add_var("range", shape=(1,), axis=0, units="m")
        mux_comp.add_var("duration", shape=(1,), axis=0, units="s")
        group.promotes("mux", outputs=[("range", f"data:payload_range:{mission_name}:range")])
        group.promotes("mux", outputs=[("duration", f"data:payload_range:{mission_name}:duration")])

        self.add_subsystem(
            "contour_calc",
            group,
            promotes_inputs=["*"],
            promotes_outputs=[
                f"data:payload_range:{mission_name}:block_fuel",
                f"data:payload_range:{mission_name}:payload",
                f"data:payload_range:{mission_name}:TOW",
                f"data:payload_range:{mission_name}:range",
                f"data:payload_range:{mission_name}:duration",
            ],
        )

        return group

    def _add_payload_range_grid_group(self):

        mission_name = self.options["mission_name"]
        nb_grid_points = self.options["nb_grid_points"]

        group = om.Group()

        group.add_subsystem(
            "input_values",
            PayloadRangeGridInputValues(
                mission_name=mission_name,
                nb_points=nb_grid_points,
                random_seed=self.options["grid_random_seed"],
                min_payload_ratio=self.options["min_payload_ratio"],
                min_block_fuel_ratio=self.options["min_block_fuel_ratio"],
            ),
            promotes=["*"],
        )

        var_connections = [
            (
                f"data:payload_range:{mission_name}:grid:block_fuel",
                f"data:mission:{mission_name}:block_fuel",
            ),
            (
                f"data:payload_range:{mission_name}:grid:TOW",
                f"data:mission:{mission_name}:TOW",
            ),
        ]

        mission_wrapper = MissionWrapper(
            self.options["mission_file_path"],
            mission_name=mission_name,
            force_all_block_fuel_usage=True,
        )

        self._add_mission_runs(group, mission_wrapper, nb_grid_points, var_connections)

        mux_comp = group.add_subsystem(name="mux", subsys=om.MuxComp(vec_size=nb_grid_points))
        mux_comp.add_var("range", shape=(1,), axis=0, units="m")
        mux_comp.add_var("duration", shape=(1,), axis=0, units="s")
        group.promotes("mux", outputs=[("range", f"data:payload_range:{mission_name}:grid:range")])
        group.promotes(
            "mux", outputs=[("duration", f"data:payload_range:{mission_name}:grid:duration")]
        )

        self.add_subsystem(
            "grid_calc",
            group,
            promotes_inputs=["*"],
            promotes_outputs=[
                f"data:payload_range:{mission_name}:grid:block_fuel",
                f"data:payload_range:{mission_name}:grid:payload",
                f"data:payload_range:{mission_name}:grid:TOW",
                f"data:payload_range:{mission_name}:grid:range",
                f"data:payload_range:{mission_name}:grid:duration",
            ],
        )

        return group

    def _add_mission_runs(self, group, mission_wrapper, nb_missions, input_var_connections):

        mission_name = self.options["mission_name"]

        mission_options = {
            key: val for key, val in self.options.items() if key in MissionRun().options
        }
        mission_options["mission_file_path"] = mission_wrapper
        mission_inputs = get_variable_list_from_system(
            MissionRun(**mission_options), io_status="inputs"
        )

        first_route_name = mission_wrapper.get_route_names()[0]
        for i in range(nb_missions):
            subsys_name = f"mission_{i}"
            group.add_subsystem(subsys_name, MissionRun(**mission_options))

            # Connect block_fuel and TOW mission inputs to contour inputs
            for payload_range_var, mission_var in input_var_connections:
                group.connect(
                    payload_range_var,
                    f"{subsys_name}.{mission_var}",
                    src_indices=[i],
                )

            # All other inputs are promoted.
            promoted_inputs = [
                variable.name
                for variable in mission_inputs
                if variable.name not in [var_conn[1] for var_conn in input_var_connections]
            ]

            group.promotes(subsys_name, inputs=promoted_inputs)

            group.connect(
                f"{subsys_name}.data:mission:{mission_name}:{first_route_name}:distance",
                f"mux.range_{i}",
            )
            group.connect(
                f"{subsys_name}.data:mission:{mission_name}:{first_route_name}:duration",
                f"mux.duration_{i}",
            )


class PayloadRangeContourInputValues(om.ExplicitComponent):
    """
    This class provides input values for missions that will compute the contour
    of the payload-range diagram.
    """

    def initialize(self):
        self.options.declare(
            "mission_name",
            default=None,
            types=str,
            allow_none=True,
            desc="The mission name. Required if mission file defines several missions.",
        )
        self.options.declare(
            "nb_points",
            default=4,
            types=int,
            lower=4,
            desc='If >4, additional points are used in the final "MFW slope" of the diagram.',
        )

    def setup(self):
        mission_name = self.options["mission_name"]
        nb_points = self.options["nb_points"]

        self.add_input("data:weight:aircraft:max_payload", val=np.nan, units="kg")
        self.add_input("data:weight:aircraft:MTOW", val=np.nan, units="kg")
        self.add_input("data:weight:aircraft:OWE", val=np.nan, units="kg")
        self.add_input("data:weight:aircraft:MFW", val=np.nan, units="kg")
        self.add_input(
            f"data:mission:{mission_name}:consumed_fuel_before_input_weight",
            val=np.nan,
            units="kg",
        )

        self.add_output(
            f"data:payload_range:{mission_name}:payload", shape=(nb_points,), units="kg"
        )
        self.add_output(
            f"data:payload_range:{mission_name}:block_fuel", shape=(nb_points,), units="kg"
        )
        self.add_output(f"data:payload_range:{mission_name}:TOW", shape=(nb_points,), units="kg")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        mission_name = self.options["mission_name"]
        nb_points = self.options["nb_points"]

        max_payload = inputs["data:weight:aircraft:max_payload"]
        payload_at_max_takeoff_weight_and_max_fuel_weight = (
            self._calculate_payload_at_max_takeoff_weight_and_max_fuel_weight(inputs)
        )

        payload_values = outputs[f"data:payload_range:{mission_name}:payload"]
        block_fuel_values = outputs[f"data:payload_range:{mission_name}:block_fuel"]
        TOW_values = outputs[f"data:payload_range:{mission_name}:TOW"]

        payload_values[0:2] = max_payload
        payload_values[2:] = np.linspace(
            payload_at_max_takeoff_weight_and_max_fuel_weight.squeeze(), 0.0, nb_points - 2
        )

        block_fuel_values[0] = 0.0
        block_fuel_values[1] = self._calculate_block_fuel_at_max_takeoff_weight(inputs, max_payload)
        block_fuel_values[2:] = inputs["data:weight:aircraft:MFW"]

        TOW_values[:2] = inputs["data:weight:aircraft:MTOW"]
        TOW_values[2:] = self._calculate_takeoff_weight_at_max_fuel_weight(
            inputs, payload_values[2:]
        )

    def _calculate_block_fuel_at_max_takeoff_weight(self, inputs, payload):
        fuel_at_takeoff = (
            inputs["data:weight:aircraft:MTOW"] - payload - inputs["data:weight:aircraft:OWE"]
        )
        block_fuel_at_max_takeoff_weight = (
            fuel_at_takeoff
            + inputs[
                f"data:mission:{self.options['mission_name']}:consumed_fuel_before_input_weight"
            ]
        )
        return block_fuel_at_max_takeoff_weight

    def _calculate_takeoff_weight_at_max_fuel_weight(self, inputs, payload):
        fuel_at_takeoff = (
            inputs["data:weight:aircraft:MFW"]
            - inputs[
                f"data:mission:{self.options['mission_name']}:consumed_fuel_before_input_weight"
            ]
        )
        takeoff_weight_at_max_fuel_weight = (
            fuel_at_takeoff + payload + inputs["data:weight:aircraft:OWE"]
        )
        return takeoff_weight_at_max_fuel_weight

    def _calculate_payload_at_max_takeoff_weight_and_max_fuel_weight(self, inputs):
        consumed_fuel_before_takeoff = inputs[
            f"data:mission:{self.options['mission_name']}:consumed_fuel_before_input_weight"
        ]

        fuel_at_takeoff = inputs["data:weight:aircraft:MFW"] - consumed_fuel_before_takeoff
        payload_at_max_takeoff_weight_and_max_fuel_weight = (
            inputs["data:weight:aircraft:MTOW"]
            - fuel_at_takeoff
            - inputs["data:weight:aircraft:OWE"]
        )
        return payload_at_max_takeoff_weight_and_max_fuel_weight


class PayloadRangeGridInputValues(om.ExplicitComponent):
    """
    This class provides input values for missions that will compute points inside the contour
    of the payload-range diagram.
    """

    def initialize(self):
        self.options.declare(
            "mission_name",
            default=None,
            types=str,
            allow_none=True,
            desc="The mission name. Required if mission file defines several missions.",
        )
        self.options.declare(
            "nb_points",
            default=20,
            types=int,
            desc='If >4, additional points are used in the final "MFW slope" of the diagram.',
        )
        self.options.declare(
            "random_seed",
            default=None,
            types=int,
            allow_none=True,
            desc="Used as random state for initializing the Latin Hypercube Sampling "
            "algorithm for generating the inner grid.",
        )
        self.options.declare(
            "min_payload_ratio",
            default=0.3,
            lower=0.0,
            upper=0.9,
            desc="Sets the minimum payload for inner grid points, as a ratio w.r.t. max payload.",
        )
        self.options.declare(
            "min_block_fuel_ratio",
            default=0.3,
            lower=0.0,
            upper=0.9,
            desc="Sets the minimum block fuel for inner grid points, as a ratio w.r.t. max "
            "possible fuel weight for the current payload.",
        )

    def setup(self):
        mission_name = self.options["mission_name"]
        nb_points = self.options["nb_points"]

        self.add_input(
            f"data:payload_range:{mission_name}:payload", val=np.nan, shape_by_conn=True, units="kg"
        )
        self.add_input(
            f"data:payload_range:{mission_name}:block_fuel",
            val=np.nan,
            shape_by_conn=True,
            units="kg",
        )
        self.add_input("data:weight:aircraft:OWE", val=np.nan, units="kg")
        self.add_input(
            f"data:mission:{mission_name}:consumed_fuel_before_input_weight",
            val=np.nan,
            units="kg",
        )

        self.add_output(
            f"data:payload_range:{mission_name}:grid:payload", shape=(nb_points,), units="kg"
        )
        self.add_output(
            f"data:payload_range:{mission_name}:grid:block_fuel", shape=(nb_points,), units="kg"
        )
        self.add_output(
            f"data:payload_range:{mission_name}:grid:TOW", shape=(nb_points,), units="kg"
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        mission_name = self.options["mission_name"]
        nb_points = self.options["nb_points"]

        min_payload_ratio = self.options["min_payload_ratio"]
        min_block_fuel_ratio = self.options["min_block_fuel_ratio"]

        payload_contour_values = inputs[f"data:payload_range:{mission_name}:payload"]
        block_fuel_contour_values = inputs[f"data:payload_range:{mission_name}:block_fuel"]

        max_payload = payload_contour_values[0]
        get_max_block_fuel = interp1d(payload_contour_values[1:], block_fuel_contour_values[1:])

        x = lhs(2, samples=nb_points, random_state=self.options["random_seed"])
        payload_values = (min_payload_ratio + (1.0 - min_payload_ratio) * x[:, 1]) * max_payload
        block_fuel_values = (
            min_block_fuel_ratio + (1.0 - min_block_fuel_ratio) * x[:, 0]
        ) * get_max_block_fuel(payload_values)

        outputs[f"data:payload_range:{mission_name}:grid:payload"] = payload_values
        outputs[f"data:payload_range:{mission_name}:grid:block_fuel"] = block_fuel_values
        outputs[f"data:payload_range:{mission_name}:grid:TOW"] = self._calculate_takeoff_weight(
            inputs, payload_values, block_fuel_values
        )

    def _calculate_takeoff_weight(self, inputs, payload, block_fuel):
        fuel_at_takeoff = (
            block_fuel
            - inputs[
                f"data:mission:{self.options['mission_name']}:consumed_fuel_before_input_weight"
            ]
        )
        takeoff_weight_at_max_fuel_weight = (
            fuel_at_takeoff + payload + inputs["data:weight:aircraft:OWE"]
        )
        return takeoff_weight_at_max_fuel_weight
