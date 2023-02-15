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

from dataclasses import dataclass, field

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.datacls import MANDATORY_FIELD
from fastoad.model_base.propulsion import IPropulsion
from ..base import DEFAULT_TIME_STEP, RegisteredSegment
from ..end_of_takeoff import EndOfTakoffSegment
from ..ground_speed_change import GroundSpeedChangeSegment
from ..rotation import RotationSegment
from ...base import FlightSequence
from ...polar import Polar
from ...polar_modifier import AbstractPolarModifier, LegacyPolar


@dataclass
class TakeOffSequence(RegisteredSegment, FlightSequence):
    target: FlightPoint = MANDATORY_FIELD

    #: A IPropulsion instance that will be called at each time step.
    propulsion: IPropulsion = MANDATORY_FIELD

    #: The Polar instance that will provide drag data.
    polar: Polar = MANDATORY_FIELD

    #:
    polar_modifier: AbstractPolarModifier = LegacyPolar()

    #: The reference area, in m**2.
    reference_area: float = MANDATORY_FIELD

    thrust_rate: float = 1.0

    #: Used time step for computation (actual time step can be lower at some particular times of
    #: the flight path).
    time_step: float = DEFAULT_TIME_STEP

    #: The EngineSetting value associated to the segment. Can be used in the
    #: propulsion model.
    engine_setting: EngineSetting = EngineSetting.CLIMB

    rotation_equivalent_airspeed: float = MANDATORY_FIELD
    _rotation_target: FlightPoint = field(default=FlightPoint(), init=False)

    def __post_init__(self):
        self._rotation_target = FlightPoint(equivalent_airspeed=self.rotation_equivalent_airspeed)
        self.append(
            GroundSpeedChangeSegment(
                target=self._rotation_target,
                propulsion=self.propulsion,
                reference_area=self.reference_area,
                polar=self.polar,
                polar_modifier=self.polar_modifier,
                engine_setting=self.engine_setting,
                time_step=self.time_step,
                thrust_rate=self.thrust_rate,
            )
        )
        self.append(
            RotationSegment(
                target=FlightPoint(),
                propulsion=self.propulsion,
                reference_area=self.reference_area,
                polar=self.polar,
                polar_modifier=self.polar_modifier,
                engine_setting=self.engine_setting,
                time_step=self.time_step,
                thrust_rate=self.thrust_rate,
            )
        )
        self.append(
            EndOfTakoffSegment(
                target=self.target,
                propulsion=self.propulsion,
                reference_area=self.reference_area,
                polar=self.polar,
                polar_modifier=self.polar_modifier,
                engine_setting=self.engine_setting,
                time_step=0.05,
                thrust_rate=self.thrust_rate,
            )
        )

    @property
    def rotation_equivalent_airspeed(self) -> float:
        return self._rotation_target.equivalent_airspeed

    @rotation_equivalent_airspeed.setter
    def rotation_equivalent_airspeed(self, value: float):
        self._rotation_target.equivalent_airspeed = value
