"""
Test module for rubber_engine.py
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

import numpy as np
import pandas as pd
import pytest
from fastoad.base.flight_point import FlightPoint
from fastoad.constants import EngineSetting
from fastoad.utils.physics import Atmosphere

from ..rubber_engine import RubberEngine


def test_compute_flight_points():
    engine = RubberEngine(5, 30, 1500, 1, 0.95, 10000)  # f0=1 so that output is simply fc/f0

    # Test with scalars
    flight_point = FlightPoint(
        mach=0, altitude=0, engine_setting=EngineSetting.TAKEOFF, thrust_rate=0.8
    )  # with engine_setting as EngineSetting
    engine.compute_flight_points(flight_point)
    np.testing.assert_allclose(flight_point.thrust, 0.9553 * 0.8, rtol=1e-4)
    np.testing.assert_allclose(flight_point.sfc, 0.99210e-5, rtol=1e-4)

    flight_point = FlightPoint(
        mach=0.3, altitude=0, engine_setting=EngineSetting.CLIMB.value, thrust=0.35677
    )  # with engine_setting as int
    engine.compute_flight_points(flight_point)
    np.testing.assert_allclose(flight_point.thrust_rate, 0.5, rtol=1e-4)
    np.testing.assert_allclose(flight_point.sfc, 1.3496e-5, rtol=1e-4)

    # Test full arrays
    # 2D arrays are used, where first line is for thrust rates, and second line
    # is for thrust values.
    # As thrust rates and thrust values match, thrust rate results are 2 equal
    # lines and so are thrust value results.
    machs = [0, 0.3, 0.3, 0.8, 0.8]
    altitudes = [0, 0, 0, 10000, 13000]
    thrust_rates = [0.8, 0.5, 0.5, 0.4, 0.7]
    thrusts = [0.9553 * 0.8, 0.38851, 0.35677, 0.09680, 0.11273]
    engine_settings = [
        EngineSetting.TAKEOFF,
        EngineSetting.TAKEOFF,
        EngineSetting.CLIMB,
        EngineSetting.IDLE,
        EngineSetting.CRUISE.value,
    ]  # mix EngineSetting with integers
    expected_sfc = [0.99210e-5, 1.3496e-5, 1.3496e-5, 1.8386e-5, 1.5957e-5]

    flight_points = pd.DataFrame()
    flight_points["mach"] = machs + machs
    flight_points["altitude"] = altitudes + altitudes
    flight_points["engine_setting"] = engine_settings + engine_settings
    flight_points["thrust_is_regulated"] = [False] * 5 + [True] * 5
    flight_points["thrust_rate"] = thrust_rates + [0.0] * 5
    flight_points["thrust"] = [0.0] * 5 + thrusts
    engine.compute_flight_points(flight_points)
    np.testing.assert_allclose(flight_points.sfc, expected_sfc + expected_sfc, rtol=1e-4)
    np.testing.assert_allclose(flight_points.thrust_rate, thrust_rates + thrust_rates, rtol=1e-4)
    np.testing.assert_allclose(flight_points.thrust, thrusts + thrusts, rtol=1e-4)


def test_installed_weight():
    fj44 = RubberEngine(0, 0, 0, 8452, 0, 0)
    np.testing.assert_allclose(fj44.installed_weight(), 225, atol=1)
    br710 = RubberEngine(0, 0, 0, 66034, 0, 0)
    np.testing.assert_allclose(br710.installed_weight(), 1759, atol=1)
    cfm56_3c1 = RubberEngine(0, 0, 0, 104533, 0, 0)
    np.testing.assert_allclose(cfm56_3c1.installed_weight(), 2546, atol=1)
    trent900 = RubberEngine(0, 0, 0, 340289, 0, 0)
    np.testing.assert_allclose(trent900.installed_weight(), 6535, atol=1)


def test_length():
    engine = RubberEngine(0, 0, 0, 75000, 0.95, 0)
    np.testing.assert_allclose(engine.length(), 2.73, atol=1e-2)

    engine = RubberEngine(0, 0, 0, 250000, 0.92, 0)
    np.testing.assert_allclose(engine.length(), 4.39, atol=1e-2)


def test_nacelle_diameter():
    engine = RubberEngine(3, 0, 0, 75000, 0, 0)
    np.testing.assert_allclose(engine.nacelle_diameter(), 1.61, atol=1e-2)

    engine = RubberEngine(5.5, 0, 0, 250000, 0, 0)
    np.testing.assert_allclose(engine.nacelle_diameter(), 3.25, atol=1e-2)


def test_max_thrust():
    """
    Checks model against simplified (but analytically equivalent) formulas
    as in p. 59 of :cite:`roux:2005`, but with correct coefficients (yes, those in report
    are not consistent with the complete formula nor the figure 2.19 just below)

    .. bibliography:: ../refs.bib
    """
    engine = RubberEngine(5, 30, 1500, 1, 0, 0)  # f0=1 so that output is simply fmax/f0
    machs = np.arange(0, 1.01, 0.1)

    # Check with cruise altitude
    atm = Atmosphere(11000, altitude_in_feet=False)
    max_thrust_ratio = engine.max_thrust(atm, machs, -100)
    ref_max_thrust_ratio = (
        0.94916 * atm.density / 1.225 * (1 - 0.68060 * machs + 0.51149 * machs ** 2)
    )
    np.testing.assert_allclose(max_thrust_ratio, ref_max_thrust_ratio, rtol=1e-4)

    # Check with Takeoff altitude
    atm = Atmosphere(0, altitude_in_feet=False)
    max_thrust_ratio = engine.max_thrust(atm, machs, 0)
    ref_max_thrust_ratio = (
        0.9553 * atm.density / 1.225 * (1 - 0.72971 * machs + 0.35886 * machs ** 2)
    )
    np.testing.assert_allclose(max_thrust_ratio, ref_max_thrust_ratio, rtol=1e-4)

    # Check Cruise above 11000 with compression rate != 30 and bypass ratio != 5
    engine = RubberEngine(4, 35, 1500, 1, 0, 0)  # f0=1 so that output is simply fmax/f0
    atm = Atmosphere(13000, altitude_in_feet=False)
    max_thrust_ratio = engine.max_thrust(atm, machs, -50)
    ref_max_thrust_ratio = (
        0.96880 * atm.density / 1.225 * (1 - 0.63557 * machs + 0.52108 * machs ** 2)
    )
    np.testing.assert_allclose(max_thrust_ratio, ref_max_thrust_ratio, rtol=1e-4)

    # Check with compression rate != 30 and bypass ratio != 5 and an array for altitudes (as
    # many values as mach numbers)
    engine = RubberEngine(6, 22, 1500, 1, 0, 0)  # f0=1 so that output is simply fmax/f0
    atm = Atmosphere(np.arange(3000, 13100, 1000), altitude_in_feet=False)
    max_thrust_ratio = engine.max_thrust(atm, machs, -50)
    ref_max_thrust_ratio = [
        0.69811,
        0.59162,
        0.50117,
        0.42573,
        0.36417,
        0.31512,
        0.27704,
        0.24820,
        0.22678,
        0.19965,
        0.17795,
    ]
    np.testing.assert_allclose(max_thrust_ratio, ref_max_thrust_ratio, rtol=1e-4)


def test_sfc_at_max_thrust():
    """
    Checks model against values from :cite:`roux:2005` p.40
    (only for ground/Mach=0 values, as cruise values of the report look flawed)

    .. bibliography:: ../refs.bib
    """

    # Check with arrays
    cfm56_3c1 = RubberEngine(6, 25.7, 0, 0, 0, 0)
    atm = Atmosphere([0, 10668, 13000], altitude_in_feet=False)
    sfc = cfm56_3c1.sfc_at_max_thrust(atm, [0, 0.8, 0.8])
    # Note: value for alt==10668 is different from PhD report
    #       alt=13000 is here just for testing in stratosphere
    np.testing.assert_allclose(sfc, [0.97035e-5, 1.7756e-5, 1.7711e-5], rtol=1e-4)

    # Check with scalars
    trent900 = RubberEngine(7.14, 41, 0, 0, 0, 0)
    atm = Atmosphere(0, altitude_in_feet=False)
    sfc = trent900.sfc_at_max_thrust(atm, 0)
    np.testing.assert_allclose(sfc, 0.73469e-5, rtol=1e-4)

    atm = Atmosphere(9144, altitude_in_feet=False)
    sfc = trent900.sfc_at_max_thrust(atm, 0.8)
    np.testing.assert_allclose(sfc, 1.6766e-5, rtol=1e-4)  # value is different from PhD report

    # Check with arrays
    pw2037 = RubberEngine(6, 31.8, 0, 0, 0, 0)
    atm = Atmosphere(0, altitude_in_feet=False)
    sfc = pw2037.sfc_at_max_thrust(atm, 0)
    np.testing.assert_allclose(sfc, 0.9063e-5, rtol=1e-4)

    atm = Atmosphere(10668, altitude_in_feet=False)
    sfc = pw2037.sfc_at_max_thrust(atm, 0.85)
    np.testing.assert_allclose(sfc, 1.7439e-5, rtol=1e-4)  # value is different from PhD report


def test_sfc_ratio():
    """    Checks SFC ratio model    """
    design_alt = 10000
    engine = RubberEngine(0, 0, 0, 0, 0, design_alt)

    # Test values taken from method report (plots p. 80, see roux:2002 in refs.bib)
    # + values where original model fails (around dh=-1562.5)
    altitudes = design_alt + np.array([-2370, -1564, -1562.5, -1560, -846, 678, 2202, 3726])

    ratio = engine.sfc_ratio(altitudes, 0.8)
    assert ratio == pytest.approx(
        [1.024, 1.020, 1.020, 1.020, 1.005, 0.977, 0.948, 0.918], rel=1e-3
    )
    ratio = engine.sfc_ratio(altitudes, 0.6)
    assert ratio == pytest.approx(
        [1.074, 1.080, 1.080, 1.080, 1.044, 0.994, 0.935, 0.877], rel=1e-3
    )
    assert engine.sfc_ratio(altitudes, 1.0) == pytest.approx(1.0, rel=1e-3)

    # Because there some code differs when we have scalars:
    assert engine.sfc_ratio(design_alt - 1562.5, 0.6) == pytest.approx(1.080, rel=1e-3)
