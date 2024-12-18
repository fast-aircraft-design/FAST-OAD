#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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
from numpy.testing import assert_allclose
from scipy.constants import foot

from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.model_base.propulsion import FuelEngineSet
from fastoad.models.performances.mission.polar import Polar

from .conftest import DummyEngine
from ..altitude_change import AltitudeChangeSegment


def test_climb_fixed_altitude_at_constant_TAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    # initialisation then change instance attributes
    segment = AltitudeChangeSegment(
        target=FlightPoint(altitude=10000.0),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        engine_setting=EngineSetting.CLIMB,
    )  # not constant TAS order, as it is the default
    segment.thrust_rate = 1.0
    segment.time_step = 2.0

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=5000.0, mass=70000.0, true_airspeed=150.0)
        )  # Test with dict

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(last_point.altitude, 10000.0)
        assert_allclose(last_point.true_airspeed, 150.0)
        assert_allclose(last_point.time, 143.5, rtol=1e-2)
        assert_allclose(last_point.mass, 69713.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 20943.0, rtol=1e-3)
        assert last_point.engine_setting == EngineSetting.CLIMB

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_climb_fixed_altitude_at_constant_EAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeSegment(
        target=FlightPoint(altitude=10000.0, equivalent_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=2.0,
        engine_setting=EngineSetting.CRUISE,  # The engine model does not use this setting
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=5000.0, mass=70000.0, equivalent_airspeed=100.0)
        )

        first_point = flight_points.iloc[0]
        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(last_point.altitude, 10000.0)
        assert_allclose(last_point.equivalent_airspeed, 100.0)
        assert_allclose(last_point.ground_distance, 20915.0, rtol=1e-3)
        assert last_point.engine_setting == EngineSetting.CRUISE

        if segment.isa_offset == 0.0:
            assert_allclose(last_point.time, 145.2, rtol=1e-2)
            assert_allclose(first_point.true_airspeed, 129.0, atol=0.1)
            assert_allclose(last_point.true_airspeed, 172.3, atol=0.1)
            assert_allclose(last_point.mass, 69710.0, rtol=1e-4)

        if segment.isa_offset == 15.0:
            assert_allclose(last_point.time, 141.2, rtol=1e-2)
            assert_allclose(first_point.true_airspeed, 132.7, atol=0.1)
            assert_allclose(last_point.true_airspeed, 178.0, atol=0.1)
            assert_allclose(last_point.mass, 69718.0, rtol=1e-4)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()

    # Test with non-zero dISA
    segment.isa_offset = 15.0
    run()


def test_climb_optimal_altitude_at_fixed_TAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeSegment(
        target=FlightPoint(
            altitude=AltitudeChangeSegment.OPTIMAL_ALTITUDE, true_airspeed="constant"
        ),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=2.0,
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=5000.0, true_airspeed=250.0, mass=70000.0)
        )

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(last_point.altitude, 10085.0, atol=0.1)
        assert_allclose(last_point.true_airspeed, 250.0)
        assert_allclose(last_point.time, 84.1, rtol=1e-2)
        assert_allclose(last_point.mach, 0.8359, rtol=1e-4)
        assert_allclose(last_point.mass, 69832.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 20401.0, rtol=1e-3)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_climb_optimal_altitude_with_optimum_CL_overrun(polar, caplog):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeSegment(
        target=FlightPoint(altitude=AltitudeChangeSegment.OPTIMAL_ALTITUDE, mach="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=2.0,
        name="doomed_climb",
    )

    def run():
        start = FlightPoint(altitude=10000.0, mach=0.82, mass=70000.0)
        flight_points = segment.compute_from(start)

        # Here segment is expected to stop immediately, since optimal CL is already overrun.
        assert len(flight_points) == 1
        assert flight_points.iloc[0].altitude == start.altitude
        assert flight_points.iloc[0].mach == start.mach
        assert flight_points.iloc[0].mass == start.mass
        assert 'Target cannot be reached in "doomed_climb"' in caplog.text

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_climb_optimal_flight_level_at_fixed_TAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeSegment(
        target=FlightPoint(
            altitude=AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL, true_airspeed="constant"
        ),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=2.0,
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=5000.0, true_airspeed=250.0, mass=70000.0)
        )

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(flight_points.true_airspeed, 250.0)
        assert_allclose(last_point.altitude / foot, 32000.0, atol=0.1)
        assert_allclose(last_point.time, 78.7, rtol=1e-2)
        assert_allclose(last_point.mach, 0.8318, rtol=1e-4)
        assert_allclose(last_point.mass, 69843.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 19091.0, rtol=1e-3)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_climb_optimal_flight_level_at_fixed_mach(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeSegment(
        target=FlightPoint(altitude=AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL, mach="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
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

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_climb_target_CL_at_fixed_mach(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeSegment(
        target=FlightPoint(CL=0.4418, mach="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        time_step=2.0,
        maximum_CL=0.1,
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


def test_climb_optimal_flight_level_at_fixed_mach_with_capped_flight_level(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeSegment(
        target=FlightPoint(altitude=AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL, mach="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=1.0,
        maximum_flight_level=300.0,
        time_step=0.01,
    )

    def run():
        flight_points = segment.compute_from(FlightPoint(altitude=5000.0, mach=0.82, mass=70000.0))

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(flight_points.mach, 0.82)
        assert_allclose(last_point.altitude / foot, 30000.0, atol=0.1)
        assert_allclose(last_point.time, 67.5, rtol=1e-2)
        assert_allclose(last_point.true_airspeed, 248.6, rtol=1e-4)
        assert_allclose(last_point.mass, 69865.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 16762.0, rtol=1e-3)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_climb_optimal_flight_level_at_fixed_mach_with_capped_flight_level_low_tolerance(polar):
    propulsion = FuelEngineSet(DummyEngine(33343.75, 5.5e-6), 2)
    CD = [
        0.020831665760852047,
        0.02084279143134122,
        0.02086141808434995,
        0.020887549371726842,
        0.02092119858687383,
        0.020962368109938546,
        0.02101107002628659,
        0.021067311011609073,
        0.021131100000781944,
        0.021202448007786045,
        0.021281362792430165,
        0.02136785617814543,
        0.021461936965202575,
        0.021563617115275917,
        0.021672909957919807,
        0.02178983193679845,
        0.021914398065850386,
        0.02204662631305294,
        0.022186538309828103,
        0.022334154257872187,
        0.02248949720014296,
        0.022652594581552537,
        0.0228234714168432,
        0.023002157966722666,
        0.02318868180707029,
        0.023383078357247743,
        0.023585381836083684,
        0.023795624119548414,
        0.024013847881133345,
        0.024240091159544883,
        0.02447439194983369,
        0.024716797545724256,
        0.024967349871284357,
        0.02522609766087809,
        0.02549308906679295,
        0.0257683716446879,
        0.026052000604529314,
        0.02634402847873117,
        0.026644509502281526,
        0.02695350319251366,
        0.027271066622039104,
        0.02759726265513164,
        0.02793215025615178,
        0.028275798925046645,
        0.028628274058123276,
        0.028989638781589933,
        0.02935996774677174,
        0.029739332549091616,
        0.0301278036489231,
        0.030525457472924972,
        0.030932372601439464,
        0.03134862365668786,
        0.03177429632034705,
        0.03220946934738221,
        0.0326542281866396,
        0.03310866154659442,
        0.03357285085976432,
        0.034046888676330114,
        0.03453086620769649,
        0.035024876877159196,
        0.03552901608707447,
        0.03604338296508885,
        0.03656806680175417,
        0.03710317516482781,
        0.03764880991771637,
        0.038205070013443386,
        0.038772066628641216,
        0.03934990302370032,
        0.03993869642884977,
        0.04053854765975828,
        0.04114957057061058,
        0.04177188180955916,
        0.04240559930532502,
        0.04305083656284694,
        0.04370772489860794,
        0.0443763735101799,
        0.045056909523094255,
        0.04574945377645506,
        0.04645414364034206,
        0.04717109669423032,
        0.04790045449915116,
        0.04864234813875698,
        0.049396899383474385,
        0.05016425025999603,
        0.05094454139803066,
        0.05173791366011771,
        0.05254450604615141,
        0.05336446034999377,
        0.05419792162513577,
        0.055045040280173235,
        0.055905959738782623,
        0.05678083599749521,
        0.05766980596072945,
        0.05857305542733898,
        0.05949069801867791,
        0.060422918136616,
        0.06136987364032966,
        0.06233171307576954,
        0.06330861432554738,
        0.064300727798259,
        0.06530824115540318,
        0.06633128152251133,
        0.06737005611885633,
        0.06842473304816289,
        0.06949547296357514,
        0.07058244955675322,
        0.07168585840543781,
        0.0728058550404989,
        0.07394263317703198,
        0.07509639025542286,
        0.07626727714992865,
        0.07745549036961259,
        0.07866122921750565,
        0.07988468740870333,
        0.0811260204740756,
        0.08238546124426614,
        0.08366318480791896,
        0.0849594016439359,
        0.08627429242889646,
        0.08760807602360568,
        0.08896092658538499,
        0.09033308439545865,
        0.09172475061950279,
        0.09313609941483886,
        0.09456734591698157,
        0.09601872388789717,
        0.09749043821855209,
        0.09898270683842877,
        0.10049575140229997,
        0.10202972650971306,
        0.10358497488737554,
        0.10516159153019,
        0.1067598781866706,
        0.10838004906100951,
        0.11002229600565712,
        0.1116869021426761,
        0.11337407608832314,
        0.1150839854806617,
        0.11681697677168955,
        0.11857318034656711,
        0.12035292775613093,
        0.12215638291315417,
        0.12398383639028011,
        0.12583548562789457,
        0.127711636099802,
        0.1296125001475494,
        0.13153831246442566,
        0.13348934872191276,
        0.1354658715529768,
        0.13746809329916476,
    ]
    CL = [
        0.0,
        0.010134228187919463,
        0.020268456375838927,
        0.03040268456375839,
        0.04053691275167785,
        0.05067114093959732,
        0.06080536912751678,
        0.07093959731543624,
        0.0810738255033557,
        0.09120805369127517,
        0.10134228187919464,
        0.11147651006711409,
        0.12161073825503356,
        0.13174496644295303,
        0.14187919463087248,
        0.15201342281879196,
        0.1621476510067114,
        0.17228187919463087,
        0.18241610738255035,
        0.1925503355704698,
        0.20268456375838928,
        0.21281879194630873,
        0.22295302013422819,
        0.23308724832214767,
        0.24322147651006712,
        0.2533557046979866,
        0.26348993288590605,
        0.27362416107382553,
        0.28375838926174496,
        0.29389261744966444,
        0.3040268456375839,
        0.31416107382550335,
        0.3242953020134228,
        0.3344295302013423,
        0.34456375838926173,
        0.3546979865771812,
        0.3648322147651007,
        0.3749664429530201,
        0.3851006711409396,
        0.3952348993288591,
        0.40536912751677856,
        0.415503355704698,
        0.42563758389261747,
        0.43577181208053695,
        0.44590604026845637,
        0.45604026845637585,
        0.46617449664429533,
        0.47630872483221476,
        0.48644295302013424,
        0.4965771812080537,
        0.5067114093959731,
        0.5168456375838927,
        0.5269798657718121,
        0.5371140939597315,
        0.5472483221476511,
        0.5573825503355705,
        0.5675167785234899,
        0.5776510067114095,
        0.5877852348993289,
        0.5979194630872483,
        0.6080536912751678,
        0.6181879194630873,
        0.6283221476510067,
        0.6384563758389262,
        0.6485906040268457,
        0.6587248322147651,
        0.6688590604026846,
        0.678993288590604,
        0.6891275167785235,
        0.699261744966443,
        0.7093959731543624,
        0.7195302013422818,
        0.7296644295302014,
        0.7397986577181208,
        0.7499328859060402,
        0.7600671140939598,
        0.7702013422818792,
        0.7803355704697986,
        0.7904697986577182,
        0.8006040268456376,
        0.8107382550335571,
        0.8208724832214765,
        0.831006711409396,
        0.8411409395973155,
        0.8512751677852349,
        0.8614093959731544,
        0.8715436241610739,
        0.8816778523489933,
        0.8918120805369127,
        0.9019463087248323,
        0.9120805369127517,
        0.9222147651006711,
        0.9323489932885907,
        0.9424832214765101,
        0.9526174496644295,
        0.962751677852349,
        0.9728859060402685,
        0.9830201342281879,
        0.9931543624161074,
        1.003288590604027,
        1.0134228187919463,
        1.0235570469798658,
        1.0336912751677854,
        1.0438255033557047,
        1.0539597315436242,
        1.0640939597315437,
        1.074228187919463,
        1.0843624161073826,
        1.0944966442953021,
        1.1046308724832214,
        1.114765100671141,
        1.1248993288590605,
        1.1350335570469798,
        1.1451677852348994,
        1.155302013422819,
        1.1654362416107382,
        1.1755704697986578,
        1.1857046979865773,
        1.1958389261744966,
        1.2059731543624161,
        1.2161073825503357,
        1.226241610738255,
        1.2363758389261745,
        1.246510067114094,
        1.2566442953020134,
        1.266778523489933,
        1.2769127516778525,
        1.2870469798657718,
        1.2971812080536913,
        1.3073154362416108,
        1.3174496644295302,
        1.3275838926174497,
        1.3377181208053692,
        1.3478523489932885,
        1.357986577181208,
        1.3681208053691276,
        1.378255033557047,
        1.3883892617449665,
        1.398523489932886,
        1.4086577181208053,
        1.4187919463087248,
        1.4289261744966444,
        1.4390604026845637,
        1.4491946308724832,
        1.4593288590604028,
        1.469463087248322,
        1.4795973154362416,
        1.4897315436241612,
        1.4998657718120805,
        1.51,
    ]

    custom_polar = Polar(CL, CD)

    start = FlightPoint(altitude=10646.28619115, mass=85977, mach=0.78)

    segment = AltitudeChangeSegment(
        target=FlightPoint(altitude=AltitudeChangeSegment.OPTIMAL_FLIGHT_LEVEL, mach="constant"),
        propulsion=propulsion,
        reference_area=156.50,
        polar=custom_polar,
        thrust_rate=1.0,
        maximum_flight_level=350.0,
        time_step=5.0,
    )

    def run():
        flight_points = segment.compute_from(start)

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(flight_points.mach, 0.78)
        assert_allclose(last_point.altitude / foot, 35000.0, atol=0.1)

    run()


def test_climb_not_enough_thrust(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeSegment(
        target=FlightPoint(altitude=10000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=120.0,
        polar=polar,
        thrust_rate=0.1,
    )
    assert (
        len(segment.compute_from(FlightPoint(altitude=5000.0, true_airspeed=150.0, mass=70000.0)))
        == 1
    )


def test_descent_to_fixed_altitude_at_constant_TAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeSegment(
        target=FlightPoint(altitude=5000.0, true_airspeed="constant"),
        propulsion=propulsion,
        reference_area=100.0,
        polar=polar,
        thrust_rate=0.1,
        time_step=2.0,
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=10000.0, true_airspeed=200.0, mass=70000.0, time=2000.0)
        )  # And we define a non-null start time

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(last_point.altitude, 5000.0)
        assert_allclose(last_point.true_airspeed, 200.0)
        assert_allclose(last_point.time, 3370.4, rtol=1e-2)
        assert_allclose(last_point.mass, 69849.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 274043.0, rtol=1e-3)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_descent_to_fixed_altitude_at_constant_EAS(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeSegment(
        target=FlightPoint(altitude=5000.0, equivalent_airspeed="constant"),
        propulsion=propulsion,
        reference_area=100.0,
        polar=polar,
        thrust_rate=0.1,
        time_step=2.0,
    )

    def run():
        flight_points = segment.compute_from(
            FlightPoint(altitude=10000.0, equivalent_airspeed=200.0, mass=70000.0)
        )

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(last_point.altitude, 5000.0)
        assert_allclose(last_point.equivalent_airspeed, 200.0)
        assert_allclose(last_point.time, 821.4, rtol=1e-2)
        assert_allclose(last_point.mass, 69910.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 243155.0, rtol=1e-3)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()


def test_descent_to_fixed_EAS_at_constant_mach(polar):
    propulsion = FuelEngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    segment = AltitudeChangeSegment(
        target=FlightPoint(equivalent_airspeed=150.0, mach="constant"),
        propulsion=propulsion,
        reference_area=100.0,
        polar=polar,
        thrust_rate=0.1,
        # time_step=5.0, # we use default time step
    )

    def run():
        flight_points = segment.compute_from(FlightPoint(altitude=10000.0, mass=70000.0, mach=0.78))

        last_point = flight_points.iloc[-1]
        # Note: reference values are obtained by running the process with 0.01s as time step
        assert_allclose(last_point.equivalent_airspeed, 150.0)
        assert_allclose(last_point.mach, 0.78)
        assert_allclose(last_point.time, 343.6, rtol=1e-2)
        assert_allclose(last_point.altitude, 8654.0, atol=1.0)
        assert_allclose(last_point.true_airspeed, 238.1, atol=0.1)
        assert_allclose(last_point.mass, 69962.0, rtol=1e-4)
        assert_allclose(last_point.ground_distance, 81042.0, rtol=1e-3)

    run()

    # A second call is done to ensure first run did not modify anything (like target definition)
    run()
