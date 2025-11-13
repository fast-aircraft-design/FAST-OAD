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

from __future__ import annotations

from dataclasses import InitVar, dataclass, field

import numpy as np
import pandas as pd
import pytest
from scipy.constants import foot, knot

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.datacls import MANDATORY_FIELD
from fastoad.model_base.propulsion import FuelEngineSet, IPropulsion
from fastoad.models.performances.mission.base import FlightSequence
from tests.dummy_plugins.dist_2.dummy_plugin_2.models.subpackage.dummy_engine import DummyEngine

from ..polar import Polar
from ..segments.registered.altitude_change import AltitudeChangeSegment
from ..segments.registered.speed_change import SpeedChangeSegment
from ..segments.registered.taxi import TaxiSegment


@pytest.fixture(scope="module")
def propulsion():
    return FuelEngineSet(DummyEngine(1.0e5, 1.0e-4), 2)


@pytest.fixture
def high_speed_polar() -> Polar:
    """Returns a dummy polar where max L/D ratio is about 16., around CL=0.5"""
    cl = np.arange(0.0, 1.5, 0.01)
    cd = 0.6e-1 * cl**2 + 0.016
    return Polar(cl, cd)


@pytest.fixture
def low_speed_polar() -> Polar:
    """Returns a dummy polar where max L/D ratio is around CL=0.5"""
    cl = np.arange(0.0, 2.0, 0.01)
    cd = 0.6e-1 * cl**2 + 0.03
    return Polar(cl, cd)


def print_dataframe(df, max_rows=20):
    """Utility for correctly printing results"""
    # Not used if all goes all well. Please keep it for future test setting/debugging.
    with pd.option_context(
        "display.max_rows", max_rows, "display.max_columns", None, "display.width", None
    ):
        print()
        print(df)


# We define here in Python the flight phases that feed the test of RangedRoute ===========
@dataclass
class AbstractManualThrustFlightPhase(FlightSequence):
    """
    Base class for climb and descent phases.
    """

    propulsion: InitVar[IPropulsion] = MANDATORY_FIELD
    reference_area: InitVar[float] = MANDATORY_FIELD
    polar: InitVar[Polar] = MANDATORY_FIELD
    thrust_rate: InitVar[float] = 1.0
    time_step: InitVar[float] = None
    segment_kwargs: dict = field(default_factory=dict, init=False)

    def __post_init__(
        self,
        propulsion: IPropulsion,
        reference_area: float,
        polar: Polar,
        thrust_rate: float,
        time_step,
    ):
        """

        :param propulsion:
        :param reference_area:
        :param polar:
        :param thrust_rate:
        :param time_step: if provided, this time step will be applied for all segments.
        """
        super().__post_init__()
        self.segment_kwargs = {
            "propulsion": propulsion,
            "reference_area": reference_area,
            "polar": polar,
            "thrust_rate": thrust_rate,
            "name": self.name,
            "time_step": time_step,
        }

    def compute_from(self, start: FlightPoint) -> pd.DataFrame | None:
        parts = []
        part_start = start
        for part in self:
            flight_points = part.compute_from(part_start)
            if len(parts) > 0:
                # First point of the segment is omitted, as it is the
                # last of previous segment.
                if len(flight_points) > 1:
                    parts.append(flight_points.iloc[1:])
            else:
                # But it is kept if the computed segment is the first one.
                parts.append(flight_points)

            part_start = FlightPoint.create(flight_points.iloc[-1])

        if parts:
            return pd.concat(parts).reset_index(drop=True)
        return None


@dataclass
class TaxiPhase(FlightSequence):
    time: InitVar[float] = MANDATORY_FIELD
    propulsion: InitVar[IPropulsion] = MANDATORY_FIELD
    thrust_rate: InitVar[float] = 0.3
    true_airspeed: InitVar[float] = 80.0

    def __post_init__(self, time, propulsion, thrust_rate, true_airspeed):
        super().__post_init__()
        self.extend(
            [
                TaxiSegment(
                    target=FlightPoint(time=time),
                    engine_setting=EngineSetting.TAKEOFF,
                    propulsion=propulsion,
                    thrust_rate=thrust_rate,
                    true_airspeed=true_airspeed,
                )
            ]
        )


@dataclass
class InitialClimbPhase(AbstractManualThrustFlightPhase):
    """
    Preset for initial climb phase.

    - Climbs up to 400ft at constant EAS
    - Accelerates to EAS = 250kt at constant altitude
    - Climbs up to 1500ft at constant EAS
    """

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)
        self.extend(
            [
                AltitudeChangeSegment(
                    target=FlightPoint(equivalent_airspeed="constant", altitude=400.0 * foot),
                    engine_setting=EngineSetting.TAKEOFF,
                    **self.segment_kwargs,
                ),
                SpeedChangeSegment(
                    target=FlightPoint(equivalent_airspeed=250.0 * knot),
                    engine_setting=EngineSetting.TAKEOFF,
                    **self.segment_kwargs,
                ),
                AltitudeChangeSegment(
                    target=FlightPoint(equivalent_airspeed="constant", altitude=1500.0 * foot),
                    engine_setting=EngineSetting.TAKEOFF,
                    **self.segment_kwargs,
                ),
            ]
        )


@dataclass
class ClimbPhase(AbstractManualThrustFlightPhase):
    """
    Preset for climb phase.

    - Climbs up to 10000ft at constant EAS
    - Accelerates to EAS = 300kt at constant altitude
    - Climbs up to target altitude at constant EAS
    """

    maximum_mach: float = field(default=5.0)
    target_altitude: float | str = MANDATORY_FIELD

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)

        self.segment_kwargs["engine_setting"] = EngineSetting.CLIMB
        self.extend(
            [
                AltitudeChangeSegment(
                    target=FlightPoint(equivalent_airspeed="constant", altitude=10000.0 * foot),
                    **self.segment_kwargs,
                ),
                SpeedChangeSegment(
                    target=FlightPoint(equivalent_airspeed=300.0 * knot), **self.segment_kwargs
                ),
                AltitudeChangeSegment(
                    target=FlightPoint(equivalent_airspeed="constant", mach=self.maximum_mach),
                    **self.segment_kwargs,
                ),
                AltitudeChangeSegment(
                    target=FlightPoint(mach="constant", altitude=self.target_altitude),
                    **self.segment_kwargs,
                ),
            ]
        )


@dataclass
class DescentPhase(AbstractManualThrustFlightPhase):
    """
    Preset for descent phase.

    - Descends down to EAS = 300kt at constant Mach
    - Descends down to 10000ft at constant EAS
    - Decelerates to EAS = 250kt
    - Descends down to target altitude at constant EAS
    """

    target_altitude: float | str = MANDATORY_FIELD

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)
        self.segment_kwargs["engine_setting"] = EngineSetting.IDLE

        self.extend(
            [
                AltitudeChangeSegment(
                    target=FlightPoint(equivalent_airspeed=300.0 * knot, mach="constant"),
                    **self.segment_kwargs,
                ),
                AltitudeChangeSegment(
                    target=FlightPoint(altitude=10000.0 * foot, equivalent_airspeed="constant"),
                    **self.segment_kwargs,
                ),
                SpeedChangeSegment(
                    target=FlightPoint(equivalent_airspeed=250.0 * knot), **self.segment_kwargs
                ),
                AltitudeChangeSegment(
                    target=FlightPoint(
                        altitude=self.target_altitude, equivalent_airspeed="constant"
                    ),
                    **self.segment_kwargs,
                ),
            ]
        )
