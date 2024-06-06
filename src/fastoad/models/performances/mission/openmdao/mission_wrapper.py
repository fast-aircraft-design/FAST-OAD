"""
Mission wrapper.
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

from os import PathLike
from typing import Dict, Optional, Tuple, Union

import numpy as np
import openmdao.api as om
import pandas as pd
from openmdao.vectors.vector import Vector

from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import IPropulsion
from ..mission_definition.mission_builder import MissionBuilder
from ..mission_definition.mission_builder.constants import NAME_TAG, TYPE_TAG
from ..mission_definition.schema import (
    CLIMB_PARTS_TAG,
    DESCENT_PARTS_TAG,
    MissionDefinition,
    PARTS_TAG,
    PHASE_TAG,
    RESERVE_TAG,
    ROUTE_TAG,
)


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


class MissionWrapper(MissionBuilder):
    """
    Wrapper around
    :class:`~fastoad.models.performances.mission.mission_definition.mission_builder.MissionBuilder`
    for using with OpenMDAO.

    Unlike its parent class, the `mission_name` argument is mandatory at instantiation, unless
    there is only one mission in the definition file.
    """

    def __init__(
        self,
        mission_definition: Union[str, PathLike, MissionDefinition],
        *,
        propulsion: IPropulsion = None,
        reference_area: float = None,
        mission_name: Optional[str] = None,
        variable_prefix: str = "data:mission",
        force_all_block_fuel_usage: bool = False,
    ):
        """
        :param mission_definition: a file path or MissionDefinition instance
        :param propulsion: if not provided, the property :attr:`propulsion` must be
                           set before calling :meth:`build`
        :param reference_area: if not provided, the property :attr:`reference_area` must be
                               set before calling :meth:`build`
        :param mission_name: name of chosen mission. Can be omitted if definition file contains
                             only one mission.
        :param variable_prefix: prefix for auto-generated variable names.
        :param force_all_block_fuel_usage: if True and if `mission_name` is provided, the mission
                                           definition will be modified to set the target fuel
                                           consumption to variable  "~:block_fuel"
        """
        super().__init__(
            mission_definition,
            propulsion=propulsion,
            reference_area=reference_area,
            mission_name=mission_name,
            variable_prefix=variable_prefix,
        )
        self.consumed_fuel_before_input_weight = 0.0
        if force_all_block_fuel_usage:
            self.force_all_block_fuel_usage()

    def force_all_block_fuel_usage(self):
        """Modifies mission definition to set block fuel as target fuel consumption."""
        if self.mission_name:
            self.definition.force_all_block_fuel_usage(self.mission_name)
            self._update_structure_builders()

    def setup(self, component: om.ExplicitComponent):
        """
        To be used during setup() of provided OpenMDAO component.

        It adds input and output variables deduced from mission definition file.

        :param component: the OpenMDAO component where the setup is done.
        """

        input_definition = self.get_input_variables(self.mission_name)
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
                _compute_vars(
                    f"{self.variable_prefix}:{part_name2}", part1.iloc[-1], part2.iloc[-1]
                )

            start_part_name = part_names[0]
            start_part = grouped_points.get_group(start_part_name)
            _compute_vars(
                f"{self.variable_prefix}:{start_part_name}", start_part.iloc[0], start_part.iloc[-1]
            )
        del flight_points["name2"]

        self.consumed_fuel_before_input_weight = mission.consumed_mass_before_input_weight
        if mission.reserve_ratio:
            outputs[self.get_reserve_variable_name()] = mission.get_reserve_fuel()

        return flight_points

    def get_reserve_variable_name(self) -> str:
        """
        :return: the name of OpenMDAO variable for fuel reserve. This name is among the declared
                 outputs in :meth:`setup`.
        """
        return f"{self.variable_prefix}:{self.mission_name}:reserve:fuel"

    def _identify_outputs(self) -> Dict[str, Tuple[str, str]]:
        """
        Builds names of OpenMDAO outputs from names of mission, route and phases.

        :return: dictionary with variable name as key and unit, description as value
        """
        output_definition = {}

        output_definition.update(self._add_vars(self.mission_name))

        for part in self._structure_builders[self.mission_name].structure[PARTS_TAG]:
            if RESERVE_TAG in part:
                output_definition[self.get_reserve_variable_name()] = (
                    "kg",
                    f'reserve fuel for mission "{self.mission_name}"',
                )
            elif part[TYPE_TAG] == PHASE_TAG:
                subpart_name = part[NAME_TAG]
                output_definition.update(self._add_vars(subpart_name))
            elif part[TYPE_TAG] == ROUTE_TAG:
                route_name = part[NAME_TAG]
                output_definition.update(self._add_vars(route_name))
                for subpart in part[CLIMB_PARTS_TAG] + part[DESCENT_PARTS_TAG]:
                    subpart_name = subpart[NAME_TAG]
                    output_definition.update(self._add_vars(subpart_name))
                output_definition.update(self._add_vars(route_name + ":cruise"))

        return output_definition

    def _add_vars(self, part_name) -> dict:
        """
        Builds names of OpenMDAO outputs for provided mission, route and phase names.

        :param part_name: part name in the form <mission_name>:<route_name:<phase_name>, route_name
        and phase_name being independently optional.
        :return: dictionary with variable name as key and unit, description as value
        """
        output_definition = {}

        name_root = ":".join(name for name in [f"{self.variable_prefix}", part_name] if name)

        names = part_name.split(":")
        mission_name, route_name, phase_name = names + [""] * (3 - len(names))
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
