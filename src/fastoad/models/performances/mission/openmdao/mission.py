"""
FAST-OAD model for mission computation.
"""
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

import logging
from importlib.resources import path

import openmdao.api as om
import pandas as pd

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem
from . import resources
from .mission_component import MissionComponent, _get_variable_name_provider
from .mission_wrapper import MissionWrapper
from ..mission_definition.schema import MissionDefinition

_LOGGER = logging.getLogger(__name__)  # Logger for this module


@RegisterOpenMDAOSystem("fastoad.performances.mission", domain=ModelDomain.PERFORMANCE)
class Mission(om.Group):
    """
    Computes a mission as specified in mission input file.
    """

    def initialize(self):
        self.options.declare(
            "propulsion_id",
            default="",
            types=str,
            desc="(mandatory) The identifier of the propulsion wrapper.",
        )
        self.options.declare(
            "out_file",
            default="",
            types=str,
            desc="If provided, a csv file will be written at provided path with all computed "
            "flight points.",
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
            "use_initializer_iteration",
            default=True,
            types=bool,
            desc="During first solver loop, a complete mission computation can fail or consume "
            "useless CPU-time.\n"
            "When activated, this option ensures the first iteration is done using a simple,\n"
            "dummy, formula instead of the specified mission.\n"
            "Set this option to False if you do expect this model to be computed only once.",
        )
        self.options.declare(
            "adjust_fuel",
            default=True,
            types=bool,
            desc="If True, block fuel will fit fuel consumption during mission. In that case, a "
            "solver (local or global) will be needed. (see `add_solver` option for more"
            "information)\n"
            "If False, block fuel will be taken from input data.",
        )
        self.options.declare(
            "compute_input_weight",
            default=False,
            types=bool,
            desc="If True, input weight will be deduced from block fuel.\n"
            "If False, block fuel will be deduced from input weight.\n"
            "Not used (actually forced to True) if adjust_fuel is True.",
        )
        self.options.declare(
            "compute_TOW",
            default=False,
            types=bool,
            desc="(Deprecated. Replaced by compute_input_weight)\n"
            "If True, TakeOff Weight will be computed from onboard fuel at takeoff and ZFW.\n"
            "If False, block fuel will be computed from ramp weight and ZFW.\n"
            "Not used (actually forced to True) if adjust_fuel is True.",
        )
        self.options.declare(
            "add_solver",
            default=False,
            types=bool,
            desc="If True, a local solver is set for the mission computation.\n"
            "It is useful if `adjust_fuel` is set to True, or to ensure consistency between "
            "ramp weight and takeoff weight + taxi-out fuel.\n"
            "If a global solver is used, using a local solver or not should be only a question"
            "of CPU time consumption and is not expected to modify the results.",
        )
        self.options.declare(
            "is_sizing",
            default=False,
            types=bool,
            desc="If True, TOW will be considered equal to MTOW and mission payload will be "
            "considered equal to design payload.",
        )
        self.options.declare(
            "reference_area_variable",
            default="data:geometry:wing:area",
            types=str,
            desc="Defines the name of the variable for providing aircraft reference surface area.",
        )

    def setup(self):
        self.options["compute_input_weight"] = self.options["compute_TOW"]

        if "::" in self.options["mission_file_path"]:
            # The configuration file parser will have added the working directory before
            # the file name. But as the user-provided string begins with "::", we just
            # have to ignore all before "::".
            i = self.options["mission_file_path"].index("::")
            file_name = self.options["mission_file_path"][i + 2 :] + ".yml"
            with path(resources, file_name) as mission_input_file:
                self.options["mission_file_path"] = MissionDefinition(mission_input_file)
        self._mission_wrapper = MissionWrapper(self.options["mission_file_path"])
        if self.options["mission_name"] is None:
            self.options["mission_name"] = self._mission_wrapper.get_unique_mission_name()

        mission_name = self.options["mission_name"]
        self._name_provider = _get_variable_name_provider(mission_name)

        self.add_subsystem("ZFW_computation", self._get_zfw_component(mission_name), promotes=["*"])

        if self.options["adjust_fuel"]:
            self.options["compute_input_weight"] = True
            self.connect(
                self._name_provider.NEEDED_BLOCK_FUEL.value,
                self._name_provider.BLOCK_FUEL.value,
            )
        if self.options["add_solver"]:
            self.nonlinear_solver = om.NonlinearBlockGS(maxiter=30, rtol=1.0e-4, iprint=0)
            self.linear_solver = om.DirectSolver()

        if self.options["compute_input_weight"]:
            self.add_subsystem(
                "input_mass_computation",
                self._get_input_weight_component(mission_name),
                promotes=["*"],
            )

        mission_options = dict(self.options.items())
        del mission_options["adjust_fuel"]
        del mission_options["compute_input_weight"]
        del mission_options["compute_TOW"]
        del mission_options["add_solver"]
        del mission_options["mission_file_path"]
        mission_options["mission_wrapper"] = self._mission_wrapper
        mission_options["mission_name"] = mission_name

        self.add_subsystem(
            "mission_computation", MissionComponent(**mission_options), promotes=["*"]
        )
        if not self.options["compute_input_weight"]:
            self.add_subsystem(
                "block_fuel_computation",
                self._get_block_fuel_component(mission_name),
                promotes=["*"],
            )

    @property
    def flight_points(self) -> pd.DataFrame:
        """Dataframe that lists all computed flight point data."""
        return self.mission_computation.flight_points

    def _get_zfw_component(self, mission_name: str) -> om.AddSubtractComp:
        """

        :param mission_name:
        :return: component that computes Zero Fuel Weight from OWE and mission payload
        """
        if self.options["is_sizing"]:
            payload_var = "data:weight:aircraft:payload"
        else:
            payload_var = self._name_provider.PAYLOAD.value

        zfw_computation = om.AddSubtractComp()
        zfw_computation.add_equation(
            self._name_provider.ZFW.value,
            ["data:weight:aircraft:OWE", payload_var],
            units="kg",
            desc=f'Zero Fuel Weight for mission "{mission_name}"',
        )
        return zfw_computation

    def _get_input_weight_component(self, mission_name: str):
        input_weight_variable = self._mission_wrapper.get_input_weight_variable_name(mission_name)
        if not input_weight_variable:
            return None

        computation = om.AddSubtractComp()
        computation.add_equation(
            output_name=input_weight_variable,
            input_names=[
                self._name_provider.ZFW.value,
                self._name_provider.BLOCK_FUEL.value,
                self._name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value,
            ],
            units="kg",
            scaling_factors=[1, 1, -1],
            desc=f'Loaded fuel at beginning for mission "{mission_name}"',
        )

        return computation

    def _get_block_fuel_component(self, mission_name: str) -> om.AddSubtractComp:
        """

        :param mission_name:
        :return: component that computes block fuel from ramp weight and ZFW
        """
        input_weight_variable = self._mission_wrapper.get_input_weight_variable_name(mission_name)

        block_fuel_computation = om.AddSubtractComp()
        block_fuel_computation.add_equation(
            output_name=self._name_provider.BLOCK_FUEL.value,
            input_names=[
                input_weight_variable,
                self._name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value,
                self._name_provider.ZFW.value,
            ],
            units="kg",
            scaling_factors=[1, 1, -1],
            desc=f'Loaded fuel at beginning for mission "{mission_name}"',
        )

        return block_fuel_computation
