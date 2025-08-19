from numpy.testing import assert_allclose

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import FuelEngineSet

from .conftest import DummyEngine
from ..hold import HoldSegment


def test_hold(polar):
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 2.0e-5), 2)

    segment = HoldSegment(
        target=FlightPoint(time=3000.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CRUISE,  # The engine model does not use this setting
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=500.0, equivalent_airspeed=120.0, mass=60000.0)
        )

        last_point = flight_points.iloc[-1]
        assert_allclose(last_point.time, 3000.0)
        assert_allclose(last_point.altitude, 500.0)
        assert_allclose(last_point.equivalent_airspeed, 120.0, atol=0.1)
        assert_allclose(last_point.mass, 58986.5, rtol=1e-4)
        if segment.isa_offset == 0.0:
            assert_allclose(last_point.true_airspeed, 122.9, atol=0.1)
            assert_allclose(last_point.ground_distance, 368795.0, rtol=1.0e-3)
        if segment.isa_offset == 15.0:
            assert_allclose(last_point.true_airspeed, 126.1, atol=0.1)
            assert_allclose(last_point.ground_distance, 378379.0, rtol=1.0e-3)
        assert last_point.engine_setting == EngineSetting.CRUISE
        assert_allclose(last_point.CL, 0.5465, rtol=1.0e-3)
        assert_allclose(last_point.CD, 0.024936, rtol=1.0e-3)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()

    # Test with non-zero dISA
    segment.isa_offset = 15.0
    run()


def test_hold_with_additional_load(polar):
    """
    We simulate a constant 1.5g turn
    """
    propulsion = FuelEngineSet(DummyEngine(0.5e5, 2.0e-5), 2)

    segment = HoldSegment(
        target=FlightPoint(time=3000.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        load_factor=1.5,
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=500.0, equivalent_airspeed=120.0, mass=60000.0)
        )

        last_point = flight_points.iloc[-1]
        assert_allclose(last_point.time, 3000.0)
        assert_allclose(last_point.altitude, 500.0)
        assert_allclose(last_point.equivalent_airspeed, 120.0, atol=0.1)
        assert_allclose(last_point.mass, 57975.4, rtol=1e-4)
        assert_allclose(last_point.true_airspeed, 122.9, atol=0.1)
        assert_allclose(last_point.ground_distance, 368795.0, rtol=1.0e-3)

        assert_allclose(last_point.CL, 0.8058, rtol=1.0e-3)
        assert_allclose(last_point.CD, 0.04246, rtol=1.0e-3)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()
