import numpy as np
from numpy.ma.testutils import approx
from numpy.testing import assert_allclose
from scipy.constants import foot

from .conftest import DummyEngine
from fastoad.model_base.propulsion import FuelEngineSet
from fastoad.model_base import FlightPoint
from fastoad.models.performances.mission.polar import Polar
from fastoad.constants import EngineSetting
from ..altitude_change import RegulatedAltitudeChangeSegment


def test_regulated_altitude_change(polar):

    propulsion = FuelEngineSet(DummyEngine(5.0e4, 1.0e-5), 2)

    required_slope_angle = 0.1 # in rad
    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(altitude=5000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
        time_step=2.0,
        slope_angle=required_slope_angle,
        thrust_rate_out_of_bound="extrapolate"
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=1000.0, mass=70000.0, true_airspeed=150.0, thrust_is_regulated=True)
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 2s as time step
        assert_allclose(last_point.altitude, 5000.0)
        assert_allclose(last_point.true_airspeed, 150.0)

        #Check the gradient is actually constant along trajectory
        altitude_change_start = flight_points.iloc[1].altitude - flight_points.iloc[0].altitude
        calculated_altitude_change_start = flight_points.iloc[0].true_airspeed*np.sin(required_slope_angle)*2.0

        assert approx(altitude_change_start, calculated_altitude_change_start, rtol=1e-3)

        assert_allclose(flight_points.iloc[0].thrust, 99239.7, atol=1)
        assert_allclose(last_point.thrust, 101737, atol=1)

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
        thrust_rate_out_of_bound="limit"
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=1000.0, mass=70000.0, true_airspeed=150.0, thrust_is_regulated=True)
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 2s as time step
        assert_allclose(last_point.altitude, 5000.0)
        assert_allclose(last_point.true_airspeed, 150.0)

        #Check the gradient is actually constant at the beginning of the trajectory
        altitude_change_start = flight_points.iloc[1].altitude - flight_points.iloc[0].altitude
        calculated_altitude_change_start = flight_points.iloc[0].true_airspeed*np.sin(required_slope_angle)*2.0

        assert approx(altitude_change_start, calculated_altitude_change_start, rtol=1e-3)
        assert_allclose(flight_points.iloc[0].thrust, 99239.7, atol=1)
        assert_allclose(last_point.thrust, 100000, atol=1)

        # Check the gradient is lower than asked at the end of trajectory and that thrust rate is never>1
        assert last_point.slope_angle < required_slope_angle
        assert not np.any(flight_points.thrust_rate > 1)

    run()

    required_slope_angle = -0.0455

    ## Now test in descent without limiting the thrust rate
    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(altitude=1000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
        time_step=2.0,
        slope_angle=required_slope_angle,
        thrust_rate_out_of_bound="extrapolate"
    )


    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=5000.0, mass=70000.0, true_airspeed=150.0, thrust_is_regulated=True)
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 2s as time step
        assert_allclose(last_point.altitude, 1000.0)
        assert_allclose(last_point.true_airspeed, 150.0)

        #Check the gradient is actually constant at the beginning of the trajectory
        altitude_change_start = flight_points.iloc[1].altitude - flight_points.iloc[0].altitude
        calculated_altitude_change_start = flight_points.iloc[0].true_airspeed*np.sin(required_slope_angle)*2.0

        assert approx(altitude_change_start, calculated_altitude_change_start, rtol=1e-3)
        assert_allclose(flight_points.iloc[0].thrust, 2424, atol=1)
        assert_allclose(last_point.thrust, -515.9, atol=1)
        assert_allclose(flight_points.iloc[0].thrust_rate, 0.02424, rtol=1e-3)
        assert_allclose(last_point.thrust_rate, -0.00516, rtol=1e-3)

        # Add test to mass when thrust_rate < 0 to check mass is not added
        assert flight_points.iloc[-2].mass > last_point.mass

    run()

    ## Now test in descent with limit on the thrust rate
    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(altitude=1000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
        time_step=2.0,
        slope_angle=required_slope_angle,
        thrust_rate_out_of_bound="limit"
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=5000.0, mass=70000.0, true_airspeed=150.0, thrust_is_regulated=True)
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 2s as time step
        assert_allclose(last_point.altitude, 1000.0)
        assert_allclose(last_point.true_airspeed, 150.0)

        # Check the gradient is actually constant at the beginning of the trajectory
        altitude_change_start = flight_points.iloc[1].altitude - flight_points.iloc[0].altitude
        calculated_altitude_change_start = flight_points.iloc[0].true_airspeed * np.sin(required_slope_angle) * 2.0

        assert approx(altitude_change_start, calculated_altitude_change_start, rtol=1e-3)
        assert_allclose(flight_points.iloc[0].thrust, 2424, atol=1)
        assert_allclose(flight_points.iloc[0].thrust_rate, 0.02424, rtol=1e-3)

        # Check that thrust_rate is never < 0
        assert not np.any(flight_points.thrust_rate < 0 )

        # Check that the last slope angle is higher than the one provided
        assert last_point.slope_angle > required_slope_angle

    run()


def test_regulated_altitude_change_with_optimal_options(polar):
    propulsion = FuelEngineSet(DummyEngine(5.0e4, 1.0e-5), 2)

    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(altitude=RegulatedAltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL, mach="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        slope_angle=0.1,
        time_step=2.0,
    )

    def run():
        flight_points = segment.compute_from(FlightPoint(altitude=5000.0, mach=0.82, mass=70000.0))

        last_point = flight_points.iloc[-1]
        assert_allclose(flight_points.mach, 0.82)
        assert_allclose(last_point.altitude / foot, 32000.0, atol=0.1)
        assert_allclose(last_point.time, 77.5, rtol=1e-2)
        assert_allclose(last_point.true_airspeed, 246.44, rtol=1e-4)
        assert_allclose(last_point.mass, 69843.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 19179.0, rtol=1e-3)

    run()

def test_regulated_altitude_change_with_CL_limitation(polar):
    propulsion = FuelEngineSet(DummyEngine(5.0e4, 1.0e-5), 2)

    segment = RegulatedAltitudeChangeSegment(
        target=FlightPoint(CL=0.4418, mach="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        slope_angle=0.1,
        time_step=2.0,
    )

    def run():
        flight_points = segment.compute_from(FlightPoint(altitude=5000.0, mach=0.82, mass=70000.0))

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(flight_points.mach, 0.82)
        assert_allclose(last_point.altitude / foot, 32000.0, atol=0.1)
        assert_allclose(last_point.time, 77.5, rtol=1e-2)
        assert_allclose(last_point.true_airspeed, 246.44, rtol=1e-4)
        assert_allclose(last_point.mass, 69843.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 19179.0, rtol=1e-3)
        assert_allclose(last_point.CL, 0.4418, rtol=1e-3)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()