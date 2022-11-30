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


from enum import Enum
from importlib.resources import path

import numpy as np
import openmdao.api as om

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem
from fastoad.openmdao.problem import get_variable_list_from_system
from . import resources
from .mission_run import MissionRun
from .mission_wrapper import MissionWrapper
from ..mission_definition.schema import MissionDefinition


@RegisterOpenMDAOSystem("fastoad.performances.payload_range", domain=ModelDomain.PERFORMANCE)
class PayloadRange(om.Group):
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

    def setup(self):

        if "::" in self.options["mission_file_path"]:
            # The configuration file parser will have added the working directory before
            # the file name. But as the user-provided string begins with "::", we just
            # have to ignore all before "::".
            i = self.options["mission_file_path"].index("::")
            file_name = self.options["mission_file_path"][i + 2 :] + ".yml"
            with path(resources, file_name) as mission_input_file:
                self.options["mission_file_path"] = MissionDefinition(mission_input_file)

        contour_subgroup = self._get_payload_range_contour_group()
        self.add_subsystem("contour_calc", contour_subgroup, promotes=["*"])

    def _get_payload_range_contour_group(self):
        mission_name = self.options["mission_name"]

        group = om.Group()

        group.add_subsystem(
            "input_grid",
            PayloadRangeContourInputValues(mission_name=mission_name),
            promotes=["*"],
        )
        n_contour_points = 4
        for i in range(n_contour_points):
            mission_wrapper = MissionWrapper(
                self.options["mission_file_path"],
                mission_name=mission_name,
                force_all_block_fuel_usage=True,
            )

            options = dict(self.options.items())
            options["mission_file_path"] = mission_wrapper

            mission_inputs = get_variable_list_from_system(
                MissionRun(**options), io_status="inputs"
            )

            subsys_name = f"mission_{i}"
            group.add_subsystem(subsys_name, MissionRun(**options))

            # Connect block_fuel and TOW mission inputs to contour inputs
            group.connect(
                f"data:payload_range:{mission_name}:block_fuel",
                f"{subsys_name}.data:mission:{mission_name}:block_fuel",
                src_indices=[i],
            )
            group.connect(
                f"data:payload_range:{mission_name}:TOW",
                f"{subsys_name}.data:mission:{mission_name}:TOW",
                src_indices=[i],
            )

            # All other inputs are promoted.
            promoted_inputs = [
                variable.name
                for variable in mission_inputs
                if variable.name
                not in [
                    f"data:mission:{mission_name}:block_fuel",
                    f"data:mission:{mission_name}:TOW",
                ]
            ]
            group.promotes(subsys_name, inputs=promoted_inputs)

            group.connect(
                f"{subsys_name}.data:mission:{mission_name}:distance",
                f"mux.range_{i}",
            )
        mux_comp = group.add_subsystem(name="mux", subsys=om.MuxComp(vec_size=n_contour_points))
        mux_comp.add_var("range", shape=(1,), axis=0, units="m")
        group.promotes("mux", outputs=[("range", f"data:payload_range:{mission_name}:range")])

        return group


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

    def setup(self):
        mission_name = self.options["mission_name"]

        self.add_input("data:weight:aircraft:max_payload", val=np.nan, units="kg")
        self.add_input("data:weight:aircraft:MTOW", val=np.nan, units="kg")
        self.add_input("data:weight:aircraft:OWE", val=np.nan, units="kg")
        self.add_input("data:weight:aircraft:MFW", val=np.nan, units="kg")
        self.add_input(
            f"data:mission:{mission_name}:consumed_fuel_before_input_weight",
            val=np.nan,
            units="kg",
        )

        self.add_output(f"data:payload_range:{mission_name}:payload", shape=(4, 1), units="kg")
        self.add_output(f"data:payload_range:{mission_name}:block_fuel", shape=(4, 1), units="kg")
        self.add_output(f"data:payload_range:{mission_name}:TOW", shape=(4, 1), units="kg")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        mission_name = self.options["mission_name"]

        max_payload = inputs["data:weight:aircraft:max_payload"]
        outputs[f"data:payload_range:{mission_name}:payload"] = [
            max_payload,
            max_payload,
            self._calculate_payload_at_max_takeoff_weight_and_max_fuel_weight(inputs),
            0.0,
        ]

        outputs[f"data:payload_range:{mission_name}:block_fuel"][0] = 0.0
        outputs[f"data:payload_range:{mission_name}:block_fuel"][
            1
        ] = self._calculate_block_fuel_at_max_takeoff_weight(inputs, max_payload)

        outputs[f"data:payload_range:{mission_name}:block_fuel"][2:] = inputs[
            "data:weight:aircraft:MFW"
        ]

        outputs[f"data:payload_range:{mission_name}:TOW"][:2] = inputs["data:weight:aircraft:MTOW"]
        outputs[f"data:payload_range:{mission_name}:TOW"][
            2:
        ] = self._calculate_takeoff_weight_at_max_fuel_weight(
            inputs, outputs[f"data:payload_range:{mission_name}:payload"][2:]
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


def _get_variable_name_provider(mission_name):
    """Factory for enum class that provide mission variable names."""

    def get_variable_name(suffix):
        return f"data:payload_range:{mission_name}:{suffix}"

    class VariableNames(Enum):
        """Enum with mission-related variable names."""

        ZFW = get_variable_name("ZFW")
        PAYLOAD = get_variable_name("payload")
        BLOCK_FUEL = get_variable_name("block_fuel")
        NEEDED_BLOCK_FUEL = get_variable_name("needed_block_fuel")
        CONSUMED_FUEL_BEFORE_INPUT_WEIGHT = get_variable_name("consumed_fuel_before_input_weight")

    return VariableNames
