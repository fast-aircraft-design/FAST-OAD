"""
Mission wrapper.
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

from typing import Dict, Tuple

import numpy as np
import openmdao.api as om
import pandas as pd
from openmdao.vectors.vector import Vector

from fastoad.model_base import FlightPoint
from ..mission_definition.mission_builder import MissionBuilder
from ..mission_definition.schema import (
    CLIMB_PARTS_TAG,
    DESCENT_PARTS_TAG,
    MISSION_DEFINITION_TAG,
    PARTS_TAG,
    PHASE_TAG,
    RESERVE_TAG,
    ROUTE_DEFINITIONS_TAG,
    ROUTE_TAG,
)


class MissionWrapper(MissionBuilder):
    """
    Wrapper around
    :class:`~fastoad.models.performances.mission.mission_definition.mission_builder.MissionBuilder`
    for using with OpenMDAO.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mission_name = None
        self.consumed_fuel_before_input_weight = 0.0

    def setup(self, component: om.ExplicitComponent, mission_name: str = None):
        """
        To be used during setup() of provided OpenMDAO component.

        It adds input and output variables deduced from mission definition file.

        :param component: the OpenMDAO component where the setup is done.
        :param mission_name: mission name (can be omitted if only one mission is defined)
        """

        if mission_name is None:
            mission_name = self.get_unique_mission_name()
        self.mission_name = mission_name
        input_definition = self.get_input_variables(mission_name)
        output_definition = self._identify_outputs()
        output_definition = {
            name: value
            for name, value in output_definition.items()
            if name not in input_definition.names()
        }
        for variable in input_definition:
            component.add_input(**variable.get_openmdao_kwargs())

        for name, (units, desc) in output_definition.items():
            component.add_output(name, 0.0, units=units, desc=desc)

    def compute(
        self, start_flight_point: FlightPoint, inputs: Vector, outputs: Vector
    ) -> pd.DataFrame:
        """
        To be used during compute() of an OpenMDAO component.

        Builds the mission from input file, and computes it. `outputs` vector is
        filled with duration, burned fuel and covered ground distance for each
        part of the flight.

        :param start_flight_point: starting point of mission
        :param inputs: the input vector of the OpenMDAO component
        :param outputs: the output vector of the OpenMDAO component
        :return: a pandas DataFrame where column names match fields of
                 :class:`~fastoad.model_base.flight_point.FlightPoint`
        """
        mission = self.build(inputs, self.mission_name)

        def _compute_vars(name_root, start: FlightPoint, end: FlightPoint):
            """Computes duration, burned fuel and covered distance."""
            if name_root + ":duration" in outputs:
                outputs[name_root + ":duration"] = end.time - start.time
            if name_root + ":fuel" in outputs:
                outputs[name_root + ":fuel"] = start.mass - end.mass
            if name_root + ":distance" in outputs:
                outputs[name_root + ":distance"] = end.ground_distance - start.ground_distance

        flight_points = mission.compute_from(start_flight_point)
        flight_points.loc[0, "name"] = flight_points.loc[1, "name"]

        nb_levels = np.max([len(n.split(":")) for n in flight_points["name"]])
        for i in range(nb_levels):
            flight_points["name2"] = [":".join(n.split(":")[: i + 1]) for n in flight_points.name]
            grouped_points = flight_points.groupby("name2")

            part_names = pd.unique(flight_points.name2)
            for part_name1, part_name2 in zip(part_names[:-1], part_names[1:]):
                part1 = grouped_points.get_group(part_name1)
                part2 = grouped_points.get_group(part_name2)
                _compute_vars(f"data:mission:{part_name2}", part1.iloc[-1], part2.iloc[-1])

            start_part_name = part_names[0]
            start_part = grouped_points.get_group(start_part_name)
            _compute_vars(
                f"data:mission:{start_part_name}", start_part.iloc[0], start_part.iloc[-1]
            )

        del flight_points["name2"]
        self.consumed_fuel_before_input_weight = mission.consumed_mass_before_input_weight
        return flight_points

    def get_reserve_variable_name(self) -> str:
        """
        :return: the name of OpenMDAO variable for fuel reserve. This name is among the declared
                 outputs in :meth:`setup`.
        """
        return f"{self._variable_prefix}:reserve:fuel"

    def _identify_outputs(self) -> Dict[str, Tuple[str, str]]:
        """
        Builds names of OpenMDAO outputs from names of mission, route and phases.

        :return: dictionary with variable name as key and unit, description as value
        """
        output_definition = {}

        output_definition.update(self._add_vars(self.mission_name))

        for part in self.definition[MISSION_DEFINITION_TAG][self.mission_name][PARTS_TAG]:
            if PHASE_TAG in part:
                phase_name = part[PHASE_TAG]
                output_definition.update(self._add_vars(self.mission_name, phase_name=phase_name))
            elif ROUTE_TAG in part:
                route_name = part[ROUTE_TAG]
                output_definition.update(self._add_vars(self.mission_name, route_name))
                route_definition = self.definition[ROUTE_DEFINITIONS_TAG][route_name]
                for part_definition in list(
                    route_definition[CLIMB_PARTS_TAG] + route_definition[DESCENT_PARTS_TAG]
                ):
                    phase_name = part_definition[PHASE_TAG]
                    output_definition.update(
                        self._add_vars(self.mission_name, route_name, phase_name)
                    )
                output_definition.update(self._add_vars(self.mission_name, route_name, "cruise"))
            elif RESERVE_TAG in part:
                output_definition[self.get_reserve_variable_name()] = (
                    "kg",
                    f'reserve fuel for mission "{self.mission_name}"',
                )

        return output_definition

    @staticmethod
    def _add_vars(mission_name, route_name=None, phase_name=None) -> dict:
        """
        Builds names of OpenMDAO outputs for provided mission, route and phase names.

        :param mission_name:
        :param route_name:
        :param phase_name:
        :return: dictionary with variable name as key and unit, description as value
        """
        output_definition = {}

        name_root = ":".join(
            name for name in ["data:mission", mission_name, route_name, phase_name] if name
        )
        if route_name and phase_name:
            flight_part_desc = (
                f'phase "{phase_name}" of route "{route_name}" in mission "{mission_name}"'
            )

        elif route_name:
            flight_part_desc = f'route "{route_name}" in mission "{mission_name}"'
        elif phase_name:
            flight_part_desc = f'phase "{phase_name}" in mission "{mission_name}"'
        else:
            flight_part_desc = f'mission "{mission_name}"'

        output_definition[name_root + ":duration"] = ("s", f"duration of {flight_part_desc}")
        output_definition[name_root + ":fuel"] = ("kg", f"burned fuel during {flight_part_desc}")
        output_definition[name_root + ":distance"] = (
            "m",
            f"covered ground distance during {flight_part_desc}",
        )

        return output_definition

    @property
    def _variable_prefix(self):
        return f"data:mission:{self.mission_name}"
