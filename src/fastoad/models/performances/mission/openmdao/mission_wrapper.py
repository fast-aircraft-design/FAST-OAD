"""
Mission wrapper.
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

from typing import Union, Dict, Tuple

import numpy as np
import openmdao.api as om
import pandas as pd
from openmdao.vectors.vector import Vector

from fastoad.base.flight_point import FlightPoint
from fastoad.models.aerodynamics.constants import POLAR_POINT_COUNT
from fastoad.models.propulsion import IPropulsion
from ..base import FlightSequence
from ..mission_definition.mission_builder import MissionBuilder
from ..mission_definition.schema import (
    MissionDefinition,
    MISSION_DEFINITION_TAG,
    STEPS_TAG,
    PHASE_TAG,
    ROUTE_TAG,
    ROUTE_DEFINITIONS_TAG,
)

BASE_UNITS = {
    "altitude": "m",
    "true_airspeed": "m/s",
    "equivalent_airspeed": "m/s",
    "range": "m",
    "time": "s",
    "ground_distance": "m",
}


class MissionWrapper:
    """
    This class builds and computes a mission from a provided definition.
    """

    def __init__(
        self,
        mission_definition: Union[str, MissionDefinition],
        propulsion: IPropulsion = None,
        reference_area: float = None,
    ):
        """
        This class builds and computes a mission from a provided definition.

        :param mission_definition: as file path or MissionDefinition instance
        :param propulsion: if not provided, the property :attr:`propulsion` must be
                           set before calling :meth:`compute`
        :param reference_area: if not provided, the property :attr:`reference_area` must be
                               set before calling :meth:`compute`
        """

        self._mission_builder: MissionBuilder = MissionBuilder(
            mission_definition, propulsion, reference_area
        )

    @property
    def propulsion(self) -> IPropulsion:
        """Propulsion model for performance computation."""
        return self._mission_builder.propulsion

    @propulsion.setter
    def propulsion(self, propulsion: IPropulsion):
        self._mission_builder.propulsion = propulsion

    @property
    def reference_area(self) -> float:
        """Reference area for aerodynamic polar."""
        return self._mission_builder.reference_area

    @reference_area.setter
    def reference_area(self, reference_area: float):
        self._mission_builder.reference_area = reference_area

    def setup(self, component: om.ExplicitComponent):
        """
        To be used during setup() of provided OpenMDAO component.

        It adds input and output variables deduced from mission definition file.

        :param component: the OpenMDAO component where the setup is done.
        """
        input_definition = {}
        self._mission_builder.identify_inputs(input_definition)
        output_definition = self._identify_outputs()
        output_definition = {
            name: value for name, value in output_definition.items() if name not in input_definition
        }
        for name, units in input_definition.items():
            if name.endswith(":CD") or name.endswith(":CL"):
                component.add_input(name, np.nan, units=units, shape=POLAR_POINT_COUNT)
            else:
                component.add_input(name, np.nan, units=units)

        for name, (units, desc) in output_definition.items():
            component.add_output(name, units=units, desc=desc)

    def compute(
        self, inputs: Vector, outputs: Vector, start_flight_point: FlightPoint
    ) -> pd.DataFrame:
        """
        To be used during compute() of an OpenMDAO component.

        Builds the mission from input file, and computes it. `outputs` vector is
        filled with duration, burned fuel and covered ground distance for each
        part of the flight.

        :param inputs: the input vector of the OpenMDAO component
        :param outputs:  the output vector of the OpenMDAO component
        :param start_flight_point: the starting flight point just after takeoff
        :return: a pandas DataFrame where columns names match
                 :meth:`fastoad.base.flight_point.FlightPoint.get_attribute_keys`
        """
        mission = self._mission_builder.build(inputs)

        def _compute_vars(name_root, start: FlightPoint, end: FlightPoint):
            """Computes duration, burned fuel and covered distance."""
            if name_root + ":duration" in outputs:
                outputs[name_root + ":duration"] = end.time - start.time
            if name_root + ":fuel" in outputs:
                outputs[name_root + ":fuel"] = start.mass - end.mass
            if name_root + ":distance" in outputs:
                outputs[name_root + ":distance"] = end.ground_distance - start.ground_distance

        if not start_flight_point.name:
            start_flight_point.name = mission.flight_sequence[0].name

        current_flight_point = start_flight_point
        flight_points = mission.compute_from(start_flight_point)
        for part in mission.flight_sequence:
            var_name_root = "data:mission:%s" % part.name
            part_end = FlightPoint(
                flight_points.loc[flight_points.name.str.startswith(part.name)].iloc[-1]
            )
            _compute_vars(var_name_root, current_flight_point, part_end)

            if isinstance(part, FlightSequence):
                # In case of a route, outputs are computed for each phase in the route
                phase_start = current_flight_point
                for phase in part.flight_sequence:
                    phase_points = flight_points.loc[flight_points.name == phase.name]
                    if len(phase_points) > 0:
                        phase_end = FlightPoint(phase_points.iloc[-1])
                        var_name_root = "data:mission:%s" % phase.name
                        _compute_vars(var_name_root, phase_start, phase_end)
                        phase_start = phase_end

            current_flight_point = part_end

        # Outputs for the whole mission
        var_name_root = "data:mission:%s" % mission.name
        _compute_vars(var_name_root, start_flight_point, current_flight_point)

        return flight_points

    def _identify_outputs(self) -> Dict[str, Tuple[str, str]]:
        """
        Builds names of OpenMDAO outputs from names of mission, route and phases.

        :return: dictionary with variable name as key and unit, description as value
        """
        output_definition = {}

        name = self._mission_builder.definition[MISSION_DEFINITION_TAG]["name"]
        output_definition.update(self._add_vars(name))

        for step in self._mission_builder.definition[MISSION_DEFINITION_TAG][STEPS_TAG]:
            if PHASE_TAG in step:
                phase_name = step[PHASE_TAG]
                output_definition.update(self._add_vars(name, phase_name=phase_name))
            else:
                route_name = step[ROUTE_TAG]
                output_definition.update(self._add_vars(name, route_name))
                route_definition = self._mission_builder.definition[ROUTE_DEFINITIONS_TAG][
                    route_name
                ]
                for step_definition in route_definition[STEPS_TAG]:
                    if PHASE_TAG in step_definition:
                        phase_name = step_definition[PHASE_TAG]
                    else:
                        phase_name = "cruise"
                    output_definition.update(self._add_vars(name, route_name, phase_name))

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
            flight_part_desc = 'phase "%s" of route "%s" in mission "%s"' % (
                phase_name,
                route_name,
                mission_name,
            )
        elif route_name:
            flight_part_desc = 'route "%s" in mission "%s"' % (route_name, mission_name,)
        elif phase_name:
            flight_part_desc = 'phase "%s" in mission "%s"' % (phase_name, mission_name,)
        else:
            flight_part_desc = 'mission "%s"' % (mission_name,)

        output_definition[name_root + ":duration"] = ("s", "duration of %s" % flight_part_desc)
        output_definition[name_root + ":fuel"] = (
            "kg",
            "burned fuel during %s" % flight_part_desc,
        )
        output_definition[name_root + ":distance"] = (
            "m",
            "covered ground distance during %s" % flight_part_desc,
        )

        return output_definition
