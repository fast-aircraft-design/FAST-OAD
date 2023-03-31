"""Class for takeoff sequence"""
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

import numpy as np

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.datacls import MANDATORY_FIELD
from fastoad.model_base.propulsion import IPropulsion
from .end_of_takeoff import EndOfTakeoffSegment
from .rotation import RotationSegment
from ..base import RegisterSegment
from ..ground_speed_change import GroundSpeedChangeSegment
from ...base import FlightSequence
from ...polar import Polar
from ...polar_modifier import AbstractPolarModifier, UnchangedPolar


@RegisterSegment("takeoff")
@dataclass
class TakeOffSequence(FlightSequence):
    """
    This class does a time-step simulation of a full takeoff:

    - ground speed acceleration up to :attr:`rotation_equivalent_airspeed`
    - rotation
    - climb up to altitude provided in :attr:`target` (safety altitude)
    """

    # This field will be used to instantiate sub-segments. Its values are synced with field
    # values in __setattr__.
    # It has to be defined first for __setattr__ to work when instantiating.
    _segment_kwargs: dict = field(default_factory=dict, init=False, repr=False)

    # This field has to be created before any call to __setattr__

    #: Target flight point for end of takeoff
    target: FlightPoint = MANDATORY_FIELD

    #: A IPropulsion instance that will be called at each time step.
    propulsion: IPropulsion = MANDATORY_FIELD

    #: The Polar instance that will provide drag data.
    polar: Polar = MANDATORY_FIELD

    #: PolarModifier instance that defines the ground effect.
    polar_modifier: AbstractPolarModifier = field(default_factory=UnchangedPolar)

    #: Reference area, in m**2.
    reference_area: float = MANDATORY_FIELD

    #: EngineSetting value associated to the sequence. Can be used in the
    #: propulsion model.
    engine_setting: EngineSetting = EngineSetting.CLIMB

    #: Imposed thrust rate for the whole sequence.
    thrust_rate: float = 1.0

    # This field is the container for the rotation_equivalent_airspeed below
    # (has to be declared first)
    _rotation_target: FlightPoint = field(default_factory=FlightPoint, init=False)

    #: Equivalent airspeed to reach for starting aircraft rotation.
    rotation_equivalent_airspeed: float = MANDATORY_FIELD

    #: Rotation rate in radians. Default value is CS-25 specification.
    rotation_rate: float = np.radians(3)

    #: Angle of attack (in radians) where tail strike is expected. Default value
    #: is good for SMR aircraft.
    rotation_alpha_limit: float = np.radians(13.5)

    #: The temperature offset for ISA atmosphere model.
    isa_offset: float = 0.0

    #: Used time step for computing ground acceleration and rotation.
    time_step: float = 0.1

    # Used time step for computing the takeoff part after rotation.
    end_time_step: float = 0.05

    _initialized: bool = field(default=False, init=False)

    def __post_init__(self):
        self._build_sequence()
        self._initialized = True

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        if key in [
            "propulsion",
            "reference_area",
            "polar",
            "polar_modifier",
            "engine_setting",
            "thrust_rate",
            "time_step",
            "isa_offset",
        ]:
            self._segment_kwargs[key] = value
        elif key == "rotation_equivalent_airspeed":
            self._rotation_target.equivalent_airspeed = value
        else:
            return

        if self._initialized:
            # Rebuild the sequence after this update of value.
            self._build_sequence()

    def _build_sequence(self):
        # This method builds the takeoff sequence. It is called from __setattr__ each time a
        # field value is updated, so the takeoff sequence is always up-to-date.

        self.clear()

        kwargs = self._segment_kwargs.copy()

        self.append(
            GroundSpeedChangeSegment(
                name=self.name,
                target=self._rotation_target,
                **kwargs,
            )
        )
        self.append(
            RotationSegment(
                name=self.name,
                target=FlightPoint(),
                rotation_rate=self.rotation_rate,
                alpha_limit=self.rotation_alpha_limit,
                **kwargs,
            )
        )

        kwargs["time_step"] = self.end_time_step
        self.append(
            EndOfTakeoffSegment(
                name=self.name,
                target=self.target,
                **kwargs,
            )
        )
