"""
Base classes for mission-related OpenMDAO components.
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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

from abc import ABCMeta
from enum import Enum
from importlib.resources import path
from os import PathLike
from typing import Optional, Union

from openmdao.core.system import System

from fastoad.models.performances.mission.mission_definition.exceptions import (
    FastMissionFileMissingMissionNameError,
)
from fastoad.models.performances.mission.mission_definition.schema import MissionDefinition
from fastoad.models.performances.mission.openmdao import resources
from fastoad.models.performances.mission.openmdao.mission_wrapper import MissionWrapper


# pylint: disable=too-few-public-methods
class NeedsOWE(System, metaclass=ABCMeta):
    """To be inherited when Operating Weight Empty variable is used."""

    def initialize(self):
        super().initialize()
        self.options.declare(
            "OWE_variable",
            default="data:weight:aircraft:OWE",
            types=str,
            desc="Variable name for Operating Weight - Empty.",
        )


# pylint: disable=too-few-public-methods
class NeedsMTOW(System, metaclass=ABCMeta):
    """To be inherited when Max TakeOff Weight variable is used."""

    def initialize(self):
        super().initialize()
        self.options.declare(
            "MTOW_variable",
            default="data:weight:aircraft:MTOW",
            types=str,
            desc="Variable name for Maximum TakeOff Weight.",
        )


# pylint: disable=too-few-public-methods
class NeedsMFW(System, metaclass=ABCMeta):
    """To be inherited when Max Fuel Weight variable is used."""

    def initialize(self):
        super().initialize()
        self.options.declare(
            "MFW_variable",
            default="data:weight:aircraft:MFW",
            types=str,
            desc="Variable name for Maximum Fuel Weight.",
        )


class BaseMissionComp(System, metaclass=ABCMeta):
    """Base class for mission components."""

    def __init__(self, **kwargs):
        # These attributes will be updated automatically wrt to option values
        # (see method '_update_mission_wrapper')
        self._mission_wrapper: Optional[MissionWrapper] = None
        self._name_provider = None

        super().__init__(**kwargs)

    def initialize(self):
        super().initialize()
        self.options.declare(
            "propulsion_id",
            default="",
            types=str,
            desc="(mandatory) The identifier of the propulsion wrapper.",
        )
        self.options.declare(
            "mission_file_path",
            default="::sizing_mission",
            types=(str, PathLike, MissionDefinition, MissionWrapper),
            allow_none=True,
            check_valid=self._update_mission_wrapper,
            desc="The path to file that defines the mission.\n"
            'It can also begin with two colons "::" to use pre-defined missions:\n'
            '  - "::sizing_mission" : design mission for CeRAS-01\n'
            '  - "::sizing_breguet" : a simple mission with Breguet formula for cruise, and input\n'
            "    coefficients for fuel reserve and fuel consumption during climb and descent",
        )
        self.options.declare(
            "mission_name",
            default=None,
            types=str,
            allow_none=True,
            check_valid=self._update_mission_wrapper,
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
            check_valid=self._update_mission_wrapper,
            desc="How auto-generated names of variables should begin.",
        )

    @property
    def name_provider(self) -> Enum:
        """Enum class that provides mission variable names."""
        return self._name_provider

    @property
    def variable_prefix(self) -> str:
        """The prefix of variable names dedicated to the mission ."""
        return self._mission_wrapper.variable_prefix

    @property
    def mission_name(self) -> str:
        """The name of considered mission."""
        return self._mission_wrapper.mission_name

    @property
    def first_route_name(self) -> Optional[str]:
        """The name of first route (and normally the main one) in the mission."""
        try:
            return self._mission_wrapper.get_route_names()[0]
        except IndexError:
            return None

    @staticmethod
    def get_mission_definition(
        mission_file_path: Optional[Union[str, PathLike, MissionDefinition]]
    ) -> MissionDefinition:
        """

        :param mission_file_path: the file path, or an already built MissionDefinition instance.
                                  In the latter case, the returned instance will be the same object.
        :return: the MissionDefinition instance built from provided mission_file_path
        """
        if isinstance(mission_file_path, MissionDefinition):
            mission_definition = mission_file_path
        elif "::" in str(mission_file_path):
            # The configuration file parser will have added the working directory before
            # the file name. But as the user-provided string begins with "::", we just
            # have to ignore all before "::".
            mission_file_path = str(mission_file_path)
            i = mission_file_path.index("::")
            file_name = mission_file_path[i + 2 :] + ".yml"
            with path(resources, file_name) as mission_input_file:
                mission_definition = MissionDefinition(mission_input_file)
        else:
            mission_definition = MissionDefinition(mission_file_path)

        return mission_definition

    def _update_mission_wrapper(self, name, value):
        """
        This method uses the 'check_valid' feature of OptionsDictionary to update
        the mission wrapper when any option among "mission_file_path", "mission_name"
        or "variable_prefix" is updated.
        """
        if (
            "mission_file_path" not in self.options
            or "mission_name" not in self.options
            or "variable_prefix" not in self.options
            or not self.options["mission_file_path"]
        ):
            # Not fully initialized
            self._mission_wrapper = None
            return

        # We get option values, but we have to take into account that we are currently
        # in the process of modifying one of them, and that self.options is probably not
        # updated right now, hence we need to use 'name' and 'value'.
        mission_file_path = self.options["mission_file_path"]
        mission_name = self.options["mission_name"]
        variable_prefix = self.options["variable_prefix"]
        if name == "mission_file_path":
            mission_file_path = value
        elif name == "mission_name":
            mission_name = value
        else:
            variable_prefix = value

        if isinstance(mission_file_path, MissionWrapper):
            self._mission_wrapper = mission_file_path
        else:
            self._mission_wrapper = MissionWrapper(
                self.get_mission_definition(mission_file_path),
                mission_name=mission_name,
            )

        try:
            self._mission_wrapper.variable_prefix = variable_prefix
            self._name_provider = self._get_variable_name_provider()
        except FastMissionFileMissingMissionNameError:
            return

    def _get_variable_name_provider(self) -> Optional[type]:
        """Factory that returns an enum class that provide mission variable names."""

        def get_variable_name(suffix):
            return f"{self.variable_prefix}:{self.mission_name}:{suffix}"

        class VariableNames(Enum):
            """Enum with mission-related variable names."""

            ZFW = get_variable_name("ZFW")
            PAYLOAD = get_variable_name("payload")
            BLOCK_FUEL = get_variable_name("block_fuel")
            NEEDED_BLOCK_FUEL = get_variable_name("needed_block_fuel")
            CONSUMED_FUEL_BEFORE_INPUT_WEIGHT = get_variable_name(
                "consumed_fuel_before_input_weight"
            )
            SPECIFIC_BURNED_FUEL = get_variable_name("specific_burned_fuel")

        return VariableNames
