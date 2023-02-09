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

import openmdao.api as om
import pandas as pd

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem
from .base import BaseMissionComp, NeedsOWE
from .mission_run import AdvancedMissionComp

_LOGGER = logging.getLogger(__name__)  # Logger for this module


@RegisterOpenMDAOSystem("fastoad.performances.mission", domain=ModelDomain.PERFORMANCE)
class OMMission(om.Group, BaseMissionComp, NeedsOWE):
    """
    Computes a mission as specified in mission input file.
    """

    def initialize(self):
        super().initialize()
        self.options.declare(
            "out_file",
            default="",
            types=str,
            desc="If provided, a csv file will be written at provided path with all computed "
            "flight points.",
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
            default=None,
            types=bool,
            deprecation='Option "compute_TOW" is deprecated for mission module. '
            'Please use "compute_input_weight" instead.',
            desc="If True, TakeOff Weight will be computed from onboard fuel at takeoff and ZFW.\n"
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

    def setup(self):
        super().setup()

        if self.options["compute_TOW"] is not None:
            self.options["compute_input_weight"] = self.options["compute_TOW"]

        mission_options = {
            key: val for key, val in self.options.items() if key in AdvancedMissionComp().options
        }
        mission_component = AdvancedMissionComp(**mission_options)

        self.add_subsystem("ZFW_computation", self._get_zfw_component(), promotes=["*"])

        if self.options["adjust_fuel"]:
            self.options["compute_input_weight"] = True
            self.connect(
                self.name_provider.NEEDED_BLOCK_FUEL.value,
                self.name_provider.BLOCK_FUEL.value,
            )
        if self.options["add_solver"]:
            self.nonlinear_solver = om.NonlinearBlockGS(maxiter=30, rtol=1.0e-4, iprint=0)
            self.linear_solver = om.DirectSolver()

        if self.options["compute_input_weight"]:
            self.add_subsystem(
                "input_mass_computation",
                self._get_input_weight_component(),
                promotes=["*"],
            )

        self.add_subsystem("mission_computation", mission_component, promotes=["*"])
        if not self.options["compute_input_weight"]:
            self.add_subsystem(
                "block_fuel_computation",
                self._get_block_fuel_component(),
                promotes=["*"],
            )

    @property
    def flight_points(self) -> pd.DataFrame:
        """Dataframe that lists all computed flight point data."""
        return self.mission_computation.flight_points

    def _get_zfw_component(self) -> om.AddSubtractComp:
        """

        :return: component that computes Zero Fuel Weight from OWE and mission payload
        """
        mission_name = self._mission_wrapper.mission_name

        if self.options["is_sizing"]:
            payload_var = "data:weight:aircraft:payload"
        else:
            payload_var = self.name_provider.PAYLOAD.value

        zfw_computation = om.AddSubtractComp()
        zfw_computation.add_equation(
            self.name_provider.ZFW.value,
            [self.options["OWE_variable"], payload_var],
            units="kg",
            desc=f'Zero Fuel Weight for mission "{mission_name}"',
        )
        return zfw_computation

    def _get_input_weight_component(self):
        """

        :return: component that computes input weight
        """
        mission_name = self._mission_wrapper.mission_name

        input_weight_variable = self._mission_wrapper.get_input_weight_variable_name(mission_name)
        if not input_weight_variable:
            return None

        computation = om.AddSubtractComp()
        computation.add_equation(
            output_name=input_weight_variable,
            input_names=[
                self.name_provider.ZFW.value,
                self.name_provider.BLOCK_FUEL.value,
                self.name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value,
            ],
            units="kg",
            scaling_factors=[1, 1, -1],
            desc=f'Loaded fuel at beginning for mission "{mission_name}"',
        )

        return computation

    def _get_block_fuel_component(self) -> om.AddSubtractComp:
        """

        :return: component that computes block fuel from ramp weight and ZFW
        """
        mission_name = self._mission_wrapper.mission_name

        input_weight_variable = self._mission_wrapper.get_input_weight_variable_name(mission_name)

        block_fuel_computation = om.AddSubtractComp()
        block_fuel_computation.add_equation(
            output_name=self._name_provider.BLOCK_FUEL.value,
            input_names=[
                input_weight_variable,
                self.name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value,
                self.name_provider.ZFW.value,
            ],
            units="kg",
            scaling_factors=[1, 1, -1],
            desc=f'Loaded fuel at beginning for mission "{mission_name}"',
        )

        return block_fuel_computation
