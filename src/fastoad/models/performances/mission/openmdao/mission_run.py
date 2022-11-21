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
from enum import Enum
from os import makedirs, path as pth

import numpy as np
from openmdao import api as om

from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import IOMPropulsionWrapper
from fastoad.models.performances.mission.mission_definition.schema import MissionDefinition
from fastoad.models.performances.mission.openmdao.mission_wrapper import MissionWrapper
from fastoad.module_management.service_registry import RegisterPropulsion

_LOGGER = logging.getLogger(__name__)  # Logger for this module


class MissionRun(om.ExplicitComponent):
    """
    Computes a mission as specified in mission input file.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flight_points = None
        self._name_provider = None
        self._input_weight_variable_name = ""
        self._engine_wrapper = self._get_engine_wrapper()
        self._mission_wrapper = self._get_mission_wrapper()

    def initialize(self):
        self.options.declare(
            "propulsion_id",
            default="",
            types=str,
            desc="(mandatory) the identifier of the propulsion wrapper.",
        )
        self.options.declare(
            "out_file",
            default="",
            types=str,
            desc="if provided, a csv file will be written at provided path with "
            "all computed flight points.",
        )
        self.options.declare(
            "mission_file_path",
            default="::sizing_mission",
            types=(str, MissionDefinition, MissionWrapper),
            allow_none=True,
            desc="The path to file that defines the mission.",
        )
        self.options.declare(
            "mission_name",
            types=str,
            desc="The mission name. Required if mission file defines several missions.",
        )
        self.options.declare(
            "reference_area_variable",
            default="data:geometry:wing:area",
            types=str,
            desc="Defines the name of the variable for providing aircraft reference surface area.",
        )
        self.options.declare(
            "variable_prefix",
            default="data:mission",
            types=str,
            desc="How auto-generated names of variables should begin.",
        )

    def setup(self):
        self._engine_wrapper = self._get_engine_wrapper()
        self._engine_wrapper.setup(self)

        self._mission_wrapper = self._get_mission_wrapper()
        self._mission_wrapper.setup(
            self,
            self.options["mission_name"],
        )

        mission_name = self.options["mission_name"]

        self._name_provider = self.get_variable_name_provider(mission_name)
        self._input_weight_variable_name = self._mission_wrapper.get_input_weight_variable_name(
            self.options["mission_name"]
        )

        try:
            self.add_input(self.options["reference_area_variable"], np.nan, units="m**2")
        except ValueError:
            pass

        # Global mission outputs
        self.add_output(
            self._name_provider.NEEDED_BLOCK_FUEL.value,
            units="kg",
            desc=f'Needed fuel to complete mission "{mission_name}", including reserve fuel',
        )
        self.add_output(
            self._name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value,
            units="kg",
            desc=f'consumed fuel quantity before target mass defined for "{mission_name}",'
            f" if any (e.g. TakeOff Weight)",
        )

    def setup_partials(self):
        self.declare_partials(["*"], ["*"], method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        propulsion_model = self._engine_wrapper.get_model(inputs)
        reference_area = inputs[self.options["reference_area_variable"]]

        self._mission_wrapper.propulsion = propulsion_model
        self._mission_wrapper.reference_area = reference_area

        # This is the default start point, that can be overridden by using the "start"
        # segment in the mission definition.
        start_flight_point = FlightPoint(
            altitude=0.0, mass=inputs[self._input_weight_variable_name], true_airspeed=0.0
        )

        self.flight_points = self._mission_wrapper.compute(start_flight_point, inputs, outputs)

        self._compute_outputs(outputs, self.flight_points)

        self._postprocess_flight_points(self.flight_points)

    def _postprocess_flight_points(self, flight_points):
        def as_scalar(value):
            if isinstance(value, np.ndarray):
                return value.item()
            return value

        flight_points = flight_points.applymap(as_scalar)
        rename_dict = {
            field_name: f"{field_name} [{unit}]"
            for field_name, unit in FlightPoint.get_units().items()
        }
        flight_points.rename(columns=rename_dict, inplace=True)
        if self.options["out_file"]:
            makedirs(pth.dirname(self.options["out_file"]), exist_ok=True)
            flight_points.to_csv(self.options["out_file"])

        return flight_points

    def _compute_outputs(self, outputs, flight_points):
        # Final ================================================================
        start_of_mission = FlightPoint.create(flight_points.iloc[0])
        end_of_mission = FlightPoint.create(flight_points.iloc[-1])
        outputs[self._name_provider.NEEDED_BLOCK_FUEL.value] = (
            start_of_mission.mass - end_of_mission.mass
        )
        reserve_var_name = self._mission_wrapper.get_reserve_variable_name()
        if reserve_var_name in outputs:
            outputs[self._name_provider.NEEDED_BLOCK_FUEL.value] += outputs[
                self._mission_wrapper.get_reserve_variable_name()
            ]
        outputs[
            self._name_provider.CONSUMED_FUEL_BEFORE_INPUT_WEIGHT.value
        ] = self._mission_wrapper.consumed_fuel_before_input_weight

    def _get_engine_wrapper(self) -> IOMPropulsionWrapper:
        """
        Overloading this method allows to define the engine without relying on the propulsion
        option.

        (useful for tests)

        :return: the engine wrapper instance
        """
        return RegisterPropulsion.get_provider(self.options["propulsion_id"])

    def _get_mission_wrapper(self) -> MissionWrapper:
        if isinstance(self.options["mission_file_path"], MissionWrapper):
            mission_wrapper = self.options["mission_file_path"]
        else:
            mission_wrapper = MissionWrapper(self.options["mission_file_path"])
        mission_wrapper.variable_prefix = self.options["variable_prefix"]
        return mission_wrapper

    def get_variable_name_provider(self, mission_name):
        """Factory for enum class that provide mission variable names."""

        def get_variable_name(suffix):
            return f"{self._mission_wrapper.variable_prefix}:{mission_name}:{suffix}"

        class VariableNames(Enum):
            """Enum with mission-related variable names."""

            ZFW = get_variable_name("ZFW")
            PAYLOAD = get_variable_name("payload")
            BLOCK_FUEL = get_variable_name("block_fuel")
            NEEDED_BLOCK_FUEL = get_variable_name("needed_block_fuel")
            CONSUMED_FUEL_BEFORE_INPUT_WEIGHT = get_variable_name(
                "consumed_fuel_before_input_weight"
            )

        return VariableNames
