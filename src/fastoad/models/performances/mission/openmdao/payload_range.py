"""Payload-Range diagram computation."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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

from dataclasses import dataclass
from typing import Dict

import numpy as np
import openmdao.api as om
from pyDOE2 import lhs
from scipy.interpolate import interp1d

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem
from fastoad.openmdao.problem import get_variable_list_from_system
from .base import BaseMissionComp, NeedsMFW, NeedsMTOW, NeedsOWE
from .mission_run import MissionComp


@RegisterOpenMDAOSystem("fastoad.performances.payload_range", domain=ModelDomain.PERFORMANCE)
class PayloadRange(om.Group, BaseMissionComp, NeedsOWE, NeedsMTOW, NeedsMFW):
    """OpenMDAO component for computing data for payload-range plots."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._contour_names = None
        self._grid_names = None

    def initialize(self):
        super().initialize()
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
            "grid_lhs_criterion",
            default="maximin",
            types=str,
            allow_none=True,
            desc="Criterion for the Latin Hypercube Sampling algorithm, as asked by pyDOE2.lhs.",
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

        # This one is declared again to change default value
        self.options.declare(
            "variable_prefix",
            default="data:payload_range",
            types=str,
            check_valid=self._update_mission_wrapper,
            desc="How auto-generated names of variables should begin.",
        )

    def setup(self):
        super().setup()
        self._contour_names = _VariableNamer(
            self.options["variable_prefix"], self.mission_name, grid=False
        )
        self._grid_names = _VariableNamer(
            self.options["variable_prefix"], self.mission_name, grid=True
        )

        self._add_payload_range_contour_group()
        if self.options["nb_grid_points"] > 0:
            self._add_payload_range_grid_group()

    def _update_mission_wrapper(self, name, value):
        super()._update_mission_wrapper(name, value)
        if self._mission_wrapper is not None:
            self._mission_wrapper.force_all_block_fuel_usage()

    def _add_payload_range_contour_group(self):
        """Creates the group for computing payload-range contour."""
        nb_contour_points = self.options["nb_contour_points"]

        group = om.Group()

        group.add_subsystem(
            "input_values",
            PayloadRangeContourInputValues(
                mission_name=self.mission_name,
                nb_points=nb_contour_points,
                PR_variable_prefix=self.variable_prefix,
            ),
            promotes=["*"],
        )

        var_connections = {"block_fuel": "block_fuel", "TOW": "TOW"}
        self._add_mission_runs(group, nb_contour_points, var_connections, "mux_contour")

        mux_comp = group.add_subsystem(
            name="mux_contour", subsys=om.MuxComp(vec_size=nb_contour_points)
        )
        mux_comp.add_var("range", shape=(1,), axis=0, units="m")
        mux_comp.add_var("duration", shape=(1,), axis=0, units="s")
        group.promotes(
            "mux_contour",
            outputs=[
                ("range", self._contour_names.range),
                ("duration", self._contour_names.duration),
            ],
        )

        self.add_subsystem(
            "contour_calc",
            group,
            promotes_inputs=["*"],
            promotes_outputs=[
                self._contour_names.block_fuel,
                self._contour_names.payload,
                self._contour_names.TOW,
                self._contour_names.range,
                self._contour_names.duration,
            ],
        )

        return group

    def _add_payload_range_grid_group(self):
        """Creates the group for computing payload-range inner grid values."""
        nb_grid_points = self.options["nb_grid_points"]

        group = om.Group()

        # Build grid inputs
        group.add_subsystem(
            "input_values",
            PayloadRangeGridInputValues(
                mission_name=self.mission_name,
                nb_points=nb_grid_points,
                PR_variable_prefix=self.variable_prefix,
                random_seed=self.options["grid_random_seed"],
                lhs_criterion=self.options["grid_lhs_criterion"],
                min_payload_ratio=self.options["min_payload_ratio"],
                min_block_fuel_ratio=self.options["min_block_fuel_ratio"],
            ),
            promotes=["*"],
        )

        # Run computations
        var_connections = {"grid:block_fuel": "block_fuel", "grid:TOW": "TOW"}
        self._add_mission_runs(group, nb_grid_points, var_connections, "mux_grid")

        # Assemble mission results in variables
        # 2 points are added to include the 2 MTOW points of the contour in the grid points.
        # (These 2 points are already added in grid inputs by PayloadRangeGridInputValues)
        mux_comp = group.add_subsystem(
            name="mux_grid", subsys=om.MuxComp(vec_size=nb_grid_points + 2)
        )
        mux_comp.add_var("range", shape=(1,), axis=0, units="m")
        mux_comp.add_var("duration", shape=(1,), axis=0, units="s")
        group.promotes(
            "mux_grid",
            outputs=[
                ("range", self._grid_names.range),
                ("duration", self._grid_names.duration),
            ],
        )

        # Adding the results of the 2 MTOW points of the contour.
        for i in range(2):
            self.connect(
                self._contour_names.range,
                f"mux_grid.range_{nb_grid_points+i}",
                src_indices=[i + 1],
            )
            self.connect(
                self._contour_names.duration,
                f"mux_grid.duration_{nb_grid_points+i}",
                src_indices=om.slicer[i + 1],
            )

        # Computation of specific burned fuel
        group.add_subsystem(
            "sbf_comp",
            om.ExecComp(
                "sbf = block_fuel / range / payload",
                block_fuel={"units": "kg", "shape_by_conn": True},
                range={"units": "NM", "copy_shape": "block_fuel"},
                payload={"units": "kg", "copy_shape": "block_fuel"},
                sbf={"units": "NM**-1", "copy_shape": "block_fuel"},
            ),
            promotes_inputs=[
                ("payload", self._grid_names.payload),
                ("range", self._grid_names.range),
                ("block_fuel", self._grid_names.block_fuel),
            ],
            promotes_outputs=[("sbf", self._grid_names.specific_burned_fuel)],
        )

        # Adding the whole group
        self.add_subsystem(
            "grid_calc",
            group,
            promotes_inputs=["*"],
            promotes_outputs=[
                self._grid_names.block_fuel,
                self._grid_names.payload,
                self._grid_names.TOW,
                self._grid_names.range,
                self._grid_names.duration,
                self._grid_names.specific_burned_fuel,
            ],
        )

        return group

    def _add_mission_runs(
        self, group: om.Group, nb_missions: int, input_var_connections: Dict[str, str], mux_name
    ):
        """Adds MissionRun components to the provided group."""

        input_var_connections = {
            self._contour_names.get_variable_name(
                name1
            ): f"data:mission:{self.mission_name}:{name2}"
            for name1, name2 in input_var_connections.items()
        }

        mission_options = {
            key: val for key, val in self.options.items() if key in MissionComp().options
        }
        # We don't want to use the same mission wrapper because we modify
        # its variable prefix.
        mission_options["mission_file_path"] = self._mission_wrapper.definition
        mission_options["variable_prefix"] = "data:mission"
        mission_inputs = get_variable_list_from_system(
            MissionComp(**mission_options), io_status="inputs"
        )

        for i in range(nb_missions):
            subsys_name = f"mission_{i}"
            group.add_subsystem(subsys_name, MissionComp(**mission_options))

            # Connect block_fuel and TOW mission inputs to contour inputs
            for payload_range_var, mission_var in input_var_connections.items():
                group.connect(
                    payload_range_var,
                    f"{subsys_name}.{mission_var}",
                    src_indices=[i],
                )

            # All other inputs are promoted.
            promoted_inputs = [
                variable.name
                for variable in mission_inputs
                if variable.name not in input_var_connections.values()
            ]

            group.promotes(subsys_name, inputs=promoted_inputs)

            group.connect(
                f"{subsys_name}.data:mission:{self.mission_name}:{self.first_route_name}:distance",
                f"{mux_name}.range_{i}",
            )
            group.connect(
                f"{subsys_name}.data:mission:{self.mission_name}:{self.first_route_name}:duration",
                f"{mux_name}.duration_{i}",
            )


class PayloadRangeContourInputValues(
    om.ExplicitComponent, BaseMissionComp, NeedsOWE, NeedsMTOW, NeedsMFW
):
    """
    This class provides input values for missions that will compute the contour
    of the payload-range diagram.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._names = None

    def initialize(self):
        super().initialize()
        self.options.declare(
            "nb_points",
            default=4,
            types=int,
            lower=4,
            desc='If >4, additional points are used in the final "MFW slope" of the diagram.',
        )
        self.options.declare(
            "PR_variable_prefix",
            default="data:payload_range",
            types=str,
            desc="How auto-generated names of payload-range variables should begin.",
        )

    def setup(self):
        super().setup()
        self._names = _VariableNamer(
            self.options["PR_variable_prefix"], self.mission_name, grid=False
        )
        nb_points = self.options["nb_points"]

        self.add_input("data:weight:aircraft:max_payload", val=np.nan, units="kg")
        self.add_input(self.options["MTOW_variable"], val=np.nan, units="kg")
        self.add_input(self.options["OWE_variable"], val=np.nan, units="kg")
        self.add_input(self.options["MFW_variable"], val=np.nan, units="kg")
        self.add_input(
            self.name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value,
            val=np.nan,
            units="kg",
        )

        self.add_output(self._names.payload, shape=(nb_points,), units="kg")
        self.add_output(self._names.block_fuel, shape=(nb_points,), units="kg")
        self.add_output(self._names.TOW, shape=(nb_points,), units="kg")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        nb_points = self.options["nb_points"]

        max_payload = inputs["data:weight:aircraft:max_payload"]
        payload_at_max_takeoff_weight_and_max_fuel_weight = (
            self._calculate_payload_at_max_takeoff_weight_and_max_fuel_weight(inputs)
        )

        payload_values = outputs[self._names.payload]
        block_fuel_values = outputs[self._names.block_fuel]
        tow_values = outputs[self._names.TOW]

        payload_values[0:2] = max_payload
        payload_values[2:] = np.linspace(
            payload_at_max_takeoff_weight_and_max_fuel_weight.squeeze(), 0.0, nb_points - 2
        )

        block_fuel_values[0] = 0.0
        block_fuel_values[1] = self._calculate_block_fuel_at_max_takeoff_weight(inputs, max_payload)
        block_fuel_values[2:] = inputs[self.options["MFW_variable"]]

        tow_values[:2] = inputs[self.options["MTOW_variable"]]
        tow_values[2:] = self._calculate_takeoff_weight_at_max_fuel_weight(
            inputs, payload_values[2:]
        )

    def _calculate_block_fuel_at_max_takeoff_weight(self, inputs, payload):
        fuel_at_takeoff = (
            inputs[self.options["MTOW_variable"]] - payload - inputs[self.options["OWE_variable"]]
        )
        block_fuel_at_max_takeoff_weight = (
            fuel_at_takeoff + inputs[self.name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value]
        )
        return block_fuel_at_max_takeoff_weight

    def _calculate_takeoff_weight_at_max_fuel_weight(self, inputs, payload):
        fuel_at_takeoff = (
            inputs[self.options["MFW_variable"]]
            - inputs[self.name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value]
        )
        takeoff_weight_at_max_fuel_weight = (
            fuel_at_takeoff + payload + inputs[self.options["OWE_variable"]]
        )
        return takeoff_weight_at_max_fuel_weight

    def _calculate_payload_at_max_takeoff_weight_and_max_fuel_weight(self, inputs):
        consumed_fuel_before_takeoff = inputs[
            self.name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value
        ]

        fuel_at_takeoff = inputs[self.options["MFW_variable"]] - consumed_fuel_before_takeoff
        payload_at_max_takeoff_weight_and_max_fuel_weight = (
            inputs[self.options["MTOW_variable"]]
            - fuel_at_takeoff
            - inputs[self.options["OWE_variable"]]
        )
        return payload_at_max_takeoff_weight_and_max_fuel_weight


class PayloadRangeGridInputValues(om.ExplicitComponent, BaseMissionComp, NeedsOWE):
    """
    This class provides input values for missions that will compute points inside the contour
    of the payload-range diagram.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._contour_names = None
        self._grid_names = None

    def initialize(self):
        super().initialize()

        self.options.declare(
            "nb_points",
            default=20,
            types=int,
            desc='If >4, additional points are used in the final "MFW slope" of the diagram.',
        )
        self.options.declare(
            "PR_variable_prefix",
            default="data:payload_range",
            types=str,
            desc="How auto-generated names of payload-range variables should begin.",
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
            "lhs_criterion",
            default="maximin",
            types=str,
            allow_none=True,
            desc="Criterion for the Latin Hypercube Sampling algorithm, as asked by pyDOE2.lhs.",
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
        super().setup()
        self._contour_names = _VariableNamer(
            self.options["PR_variable_prefix"], self.mission_name, grid=False
        )
        self._grid_names = _VariableNamer(
            self.options["PR_variable_prefix"], self.mission_name, grid=True
        )
        nb_points = self.options["nb_points"]

        self.add_input(self._contour_names.payload, val=np.nan, shape_by_conn=True, units="kg")
        self.add_input(self._contour_names.block_fuel, val=np.nan, shape_by_conn=True, units="kg")
        self.add_input(self.options["OWE_variable"], val=np.nan, units="kg")
        self.add_input(
            self.name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value, val=np.nan, units="kg"
        )

        self.add_output(self._grid_names.payload, shape=(nb_points + 2,), units="kg")
        self.add_output(self._grid_names.block_fuel, shape=(nb_points + 2,), units="kg")
        self.add_output(self._grid_names.TOW, shape=(nb_points + 2,), units="kg")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        min_payload_ratio = self.options["min_payload_ratio"]
        min_block_fuel_ratio = self.options["min_block_fuel_ratio"]

        payload_contour_values = inputs[self._contour_names.payload]
        block_fuel_contour_values = inputs[self._contour_names.block_fuel]

        max_payload = payload_contour_values[0]
        get_max_block_fuel = interp1d(payload_contour_values[1:], block_fuel_contour_values[1:])

        lhs_grid = lhs(
            2,
            criterion=self.options["lhs_criterion"],
            samples=(self.options["nb_points"]),
            random_state=self.options["random_seed"],
        )
        payload_values = (
            ((min_payload_ratio + (1.0 - min_payload_ratio) * lhs_grid[:, 1]) * max_payload),
        )
        block_fuel_values = (
            min_block_fuel_ratio + (1.0 - min_block_fuel_ratio) * lhs_grid[:, 0]
        ) * get_max_block_fuel(payload_values)

        payload_values = np.append(payload_values, payload_contour_values[1:3])
        block_fuel_values = np.append(block_fuel_values, block_fuel_contour_values[1:3])

        outputs[self._grid_names.payload] = payload_values
        outputs[self._grid_names.block_fuel] = block_fuel_values
        outputs[self._grid_names.TOW] = self._calculate_takeoff_weight(
            inputs, payload_values, block_fuel_values
        )

    def _calculate_takeoff_weight(self, inputs, payload, block_fuel):
        fuel_at_takeoff = (
            block_fuel - inputs[self.name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value]
        )
        takeoff_weight_at_max_fuel_weight = (
            fuel_at_takeoff + payload + inputs[self.options["OWE_variable"]]
        )
        return takeoff_weight_at_max_fuel_weight


@dataclass
class _VariableNamer:
    """Provides variable names."""

    variable_prefix: str
    mission_name: str
    grid: bool = False

    def get_variable_name(self, suffix: str):
        """returns variable name w.r.t. provided instance attributes."""
        grid_part = ":grid" if self.grid else ""
        return f"{self.variable_prefix}:{self.mission_name}{grid_part}:{suffix}"


# Here we add properties to _VariableNamer for convenience
def _get_property(suffix):
    def prop(self):
        return self.get_variable_name(suffix)

    return property(prop)


for main_name in [
    "payload",
    "block_fuel",
    "range",
    "duration",
    "TOW",
    "specific_burned_fuel",
]:

    setattr(_VariableNamer, main_name, _get_property(main_name))
