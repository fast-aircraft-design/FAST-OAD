from numpy.testing import assert_allclose

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import FuelEngineSet

from .conftest import DummyEngine
from ..taxi import TaxiSegment


def test_taxi():
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = TaxiSegment(
        target=FlightPoint(time=500.0),
        propulsion=propulsion,
        thrust_rate=0.1,
        true_airspeed=10.0,
        engine_setting=EngineSetting.IDLE,  # The engine model does not use this setting
    )

    def run():
        flight_points = segment.compute_from(FlightPoint(altitude=10.0, mass=50000.0, time=10000.0))

        last_point = flight_points.iloc[-1]
        assert_allclose(last_point.altitude, 10.0, atol=1.0)
        assert_allclose(last_point.time, 10500.0, rtol=1e-2)
        assert_allclose(last_point.true_airspeed, 10.0, atol=0.1)
        assert_allclose(last_point.mass, 49973.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 5000.0)
        assert last_point.engine_setting == EngineSetting.IDLE

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()
