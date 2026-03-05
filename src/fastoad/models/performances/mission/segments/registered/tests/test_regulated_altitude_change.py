import numpy as np
from numpy.testing import assert_allclose

from .conftest import DummyEngine
from fastoad.model_base.propulsion import FuelEngineSet
from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.polar import Polar
from fastoad.constants import EngineSetting
from ..regulated_altitude_change import AltitudeChangeRegulatedSegment

def test_regulated_altitude_change(polar):

    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeRegulatedSegment(
        target=FlightPoint(altitude=10000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
        time_step=2.0,
        slope_angle=0.05,
        thrust_rate_out_of_bound="extrapolate"
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=5000.0, mass=70000.0, true_airspeed=150.0, thrust_is_regulated=True)
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(last_point.altitude, 10000.0)
        assert_allclose(last_point.true_airspeed, 150.0)
        assert_allclose(last_point.thrust, 111111, atol=1)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()