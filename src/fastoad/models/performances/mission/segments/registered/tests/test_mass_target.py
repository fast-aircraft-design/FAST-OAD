from numpy.testing import assert_allclose

from fastoad.model_base import FlightPoint

from ..mass_input import MassTargetSegment


def test_dummy_target_mass():
    dummy_target_mass = MassTargetSegment(target=FlightPoint(mass=70.0e5))

    flight_points = dummy_target_mass.compute_from(
        FlightPoint(altitude=10.0, time=1000.0, mach=0.3, mass=100.0e5)
    )
    assert len(flight_points) == 1
    point = flight_points.iloc[-1]
    assert_allclose(point.altitude, 10.0, atol=1.0)
    assert_allclose(point.time, 1000.0, rtol=1e-2)
    assert_allclose(point.mach, 0.3, atol=0.001)
    assert_allclose(point.mass, 70.0e5, rtol=1e-4)
