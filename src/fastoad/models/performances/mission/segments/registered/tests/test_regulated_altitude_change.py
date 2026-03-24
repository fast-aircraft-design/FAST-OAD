import numpy as np
import pytest
from numpy.ma.testutils import approx
from numpy.testing import assert_allclose
from scipy.constants import foot

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import FuelEngineSet

from .conftest import DummyEngine
from ..altitude_change import RegulatedAltitudeChangeSegment


def test_regulated_altitude_change(polar):

    propulsion = FuelEngineSet(DummyEngine(5.0e4, 1.0e-5), 2)

    required_slope_angle = 0.1  # in rad
    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(altitude=5000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
        time_step=2.0,
        slope_angle=required_slope_angle,
        thrust_rate_out_of_bound="extrapolate",
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(
                altitude=1000.0, mass=70000.0, true_airspeed=150.0, thrust_is_regulated=True
            )
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 2s as time step
        assert_allclose(last_point.altitude, 5000.0)
        assert_allclose(last_point.true_airspeed, 150.0)
        assert_allclose(flight_points.iloc[0].thrust, 99239.7, atol=1)
        assert_allclose(last_point.thrust, 101737, atol=1)

        # Check the gradient is actually constant along trajectory
        altitude_change_start = flight_points.iloc[1].altitude - flight_points.iloc[0].altitude
        calculated_altitude_change_start = (
            flight_points.iloc[0].true_airspeed * np.sin(required_slope_angle) * 2.0
        )
        assert approx(altitude_change_start, calculated_altitude_change_start, rtol=1e-3)

    run()
    # second run as usual
    run()

    # A second call with thrust_rate limitations
    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(altitude=5000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
        time_step=2.0,
        slope_angle=required_slope_angle,
        thrust_rate_out_of_bound="limit",
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(
                altitude=1000.0, mass=70000.0, true_airspeed=150.0, thrust_is_regulated=True
            )
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 2s as time step
        assert_allclose(last_point.altitude, 5000.0)
        assert_allclose(last_point.true_airspeed, 150.0)
        assert_allclose(flight_points.iloc[0].thrust, 99239.7, atol=1)
        assert_allclose(last_point.thrust, 100000, atol=1)

        # Check the gradient is actually constant at the beginning of the trajectory
        altitude_change_start = flight_points.iloc[1].altitude - flight_points.iloc[0].altitude
        calculated_altitude_change_start = (
            flight_points.iloc[0].true_airspeed * np.sin(required_slope_angle) * 2.0
        )
        assert approx(altitude_change_start, calculated_altitude_change_start, rtol=1e-3)

        # Check the gradient is lower than asked at the end of trajectory and that
        # thrust rate is never>1
        assert last_point.slope_angle < required_slope_angle
        assert not np.any(flight_points.thrust_rate > 1)

    run()
    # second run as usual
    run()

    ## Now test in descent without limiting the thrust rate
    required_slope_angle = -0.0455

    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(altitude=1000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
        time_step=2.0,
        slope_angle=required_slope_angle,
        thrust_rate_out_of_bound="extrapolate",
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(
                altitude=5000.0, mass=70000.0, true_airspeed=150.0, thrust_is_regulated=True
            )
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 2s as time step
        assert_allclose(last_point.altitude, 1000.0)
        assert_allclose(last_point.true_airspeed, 150.0)

        # Check the gradient is actually constant at the beginning of the trajectory
        altitude_change_start = flight_points.iloc[1].altitude - flight_points.iloc[0].altitude
        calculated_altitude_change_start = (
            flight_points.iloc[0].true_airspeed * np.sin(required_slope_angle) * 2.0
        )
        assert approx(altitude_change_start, calculated_altitude_change_start, rtol=1e-3)

        # Test the thrust required is negative at the end of the trajectory
        assert_allclose(flight_points.iloc[0].thrust, 2424, atol=1)
        assert_allclose(last_point.thrust, -515.9, atol=1)
        assert_allclose(flight_points.iloc[0].thrust_rate, 0.02424, rtol=1e-3)
        assert_allclose(last_point.thrust_rate, -0.00516, rtol=1e-3)

        # Test to mass when thrust_rate < 0 to check mass is not added
        assert flight_points.iloc[-2].mass > last_point.mass

    run()
    # Second run
    run()

    ## Now test in descent with limitation on the thrust rate
    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(altitude=1000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
        time_step=2.0,
        slope_angle=required_slope_angle,
        thrust_rate_out_of_bound="limit",
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(
                altitude=5000.0, mass=70000.0, true_airspeed=150.0, thrust_is_regulated=True
            )
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 2s as time step
        assert_allclose(last_point.altitude, 1000.0)
        assert_allclose(last_point.true_airspeed, 150.0)

        # Check the gradient is actually constant at the beginning of the trajectory
        altitude_change_start = flight_points.iloc[1].altitude - flight_points.iloc[0].altitude
        calculated_altitude_change_start = (
            flight_points.iloc[0].true_airspeed * np.sin(required_slope_angle) * 2.0
        )
        assert approx(altitude_change_start, calculated_altitude_change_start, rtol=1e-3)

        assert_allclose(flight_points.iloc[0].thrust, 2424, atol=1)
        assert_allclose(flight_points.iloc[0].thrust_rate, 0.02424, rtol=1e-3)

        # Check that thrust_rate is never < 0
        assert not np.any(flight_points.thrust_rate < 0)

        # Check that the last slope angle is higher than the one provided
        assert last_point.slope_angle > required_slope_angle

    run()
    # second run
    run()

    # Test that starting with negative thrust rate and limitation,
    # it switches to manual thrust with thrust_rate = 0

    required_slope_angle = -0.1

    def run():
        flight_points = segment.compute_from(
            FlightPoint(
                altitude=5000.0, mass=70000.0, true_airspeed=150.0, thrust_is_regulated=True
            )
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 2s as time step
        assert_allclose(last_point.altitude, 1000.0)
        assert_allclose(last_point.true_airspeed, 150.0)
        assert_allclose(flight_points.thrust_rate, 0, atol=1e-6)

        run()
        # second call
        run()

def test_change_of_thrust_rate_limitation(polar):
    """ Check that changes on thrust rate limitations are effective """

    propulsion = FuelEngineSet(DummyEngine(5.0e4, 1.0e-5), 2)
    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(altitude=5000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
        time_step=2.0,
        slope_angle=0.1,
        thrust_rate_out_of_bound="limit",
        upper_thrust_rate_limit=0.9
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(
                altitude=1000.0, mass=70000.0, true_airspeed=150.0, thrust_is_regulated=True
            )
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 2s as time step
        assert_allclose(last_point.altitude, 5000.0)
        assert_allclose(last_point.true_airspeed, 150.0)

        assert_allclose(last_point.thrust, 100000*0.9, atol=1)

        # Check the gradient is lower than asked at the end of trajectory and that
        # thrust rate is never>1
        assert not np.any(flight_points.thrust_rate > 0.9)

    run()
    # second run as usual
    run()

    # Same for descent and lower thrust limit
    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(altitude=1000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
        time_step=2.0,
        slope_angle=-0.1,
        thrust_rate_out_of_bound="limit",
        lower_thrust_rate_limit=0.05
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(
                altitude=5000.0, mass=70000.0, true_airspeed=150.0, thrust_is_regulated=True
            )
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 2s as time step
        assert_allclose(last_point.altitude, 1000.0)
        assert_allclose(last_point.true_airspeed, 150.0)
        assert_allclose(flight_points.thrust_rate, 0.05, rtol=1e-6)

        run()
        # second call
        run()


def test_invalid_thrust_rate_limitation(polar):
    """Test an error is raised when thrust rate option is invalid"""
    propulsion = FuelEngineSet(DummyEngine(5.0e4, 1.0e-5), 2)

    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(altitude=1000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
        time_step=2.0,
        slope_angle=0.1,
        thrust_rate_out_of_bound="something",
    )

    expected_msg = (
        "The value of option 'thrust_rate_out_of_bound' in regulated_altitude_change is invalid "
        "it must be one of ['extrapolate', 'limit']"
    )

    with pytest.raises(ValueError) as exc_info:
        segment.compute_from(FlightPoint(altitude=5000.0, mach=0.82, mass=70000.0))

    assert str(exc_info.value) == expected_msg


# ------------------------------------------------------------------------------------
# The following tests are here to ensure that we do not lose the common functionalities
# of altitude change
# -------------------------------------------------------------------------------------


def test_regulated_altitude_change_optimal_no_limit(polar):
    """Baseline case - no thrust-rate limitation."""
    propulsion = FuelEngineSet(DummyEngine(5.0e4, 1.0e-5), 2)

    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(
            altitude=RegulatedAltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL,
            mach="constant",
        ),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        slope_angle=0.1,
        time_step=2.0,
    )

    # Execute the segment
    flight_points = segment.compute_from(FlightPoint(altitude=5000.0, mach=0.82, mass=70000.0))
    last_point = flight_points.iloc[-1]

    # Assertions
    assert_allclose(flight_points.mach, 0.82)
    assert_allclose(last_point.altitude / foot, 32000.0, atol=0.1)
    assert_allclose(last_point.time, 186.9, rtol=1e-2)
    assert_allclose(last_point.true_airspeed, 246.44, rtol=1e-4)
    assert_allclose(last_point.mass, 69808.3, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 47377.4, rtol=1e-3)


def test_regulated_altitude_change_optimal_with_limit(polar):
    """Same flight profile, but the thrust-rate is forced to stay < 1."""
    propulsion = FuelEngineSet(DummyEngine(5.0e4, 1.0e-5), 2)

    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(
            altitude=RegulatedAltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL,
            mach="constant",
        ),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        slope_angle=0.1,
        time_step=2.0,
        thrust_rate_out_of_bound="limit",
    )

    # Execute the segment
    flight_points = segment.compute_from(FlightPoint(altitude=5000.0, mach=0.82, mass=70000.0))
    last_point = flight_points.iloc[-1]

    # Assertions
    assert_allclose(flight_points.mach, 0.82)
    assert_allclose(last_point.altitude / foot, 32000.0, atol=0.1)
    assert_allclose(last_point.time, 192.2, rtol=1e-2)
    assert_allclose(last_point.true_airspeed, 246.44, rtol=1e-4)
    assert_allclose(last_point.mass, 69807.8, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 48758.2, rtol=1e-3)

    # The regulated thrust segment should have been replaced by a manual one,
    # therefore the thrust rate must be capped at 1.0.
    assert_allclose(flight_points.thrust_rate, 1.0, rtol=1e-6)


def test_regulated_altitude_change_with_CL_limitation(polar):
    """Flight is limited by a target lift coefficient (CL)."""
    propulsion = FuelEngineSet(DummyEngine(5.0e4, 1.0e-5), 2)

    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(CL=0.4418, mach="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        slope_angle=0.1,
        time_step=2.0,
    )

    # Execute the segment
    flight_points = segment.compute_from(FlightPoint(altitude=5000.0, mach=0.82, mass=70000.0))
    last_point = flight_points.iloc[-1]

    # Assertions (note: altitude reference is in metres here)
    assert_allclose(flight_points.mach, 0.82)
    assert_allclose(last_point.altitude, 9757.1, atol=0.1)
    assert_allclose(last_point.time, 187.07, rtol=1e-2)
    assert_allclose(last_point.true_airspeed, 246.44, rtol=1e-4)
    assert_allclose(last_point.mass, 69808.1, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 47412.3, rtol=1e-3)
    assert_allclose(last_point.CL, 0.4418, rtol=1e-3)
