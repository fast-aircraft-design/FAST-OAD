"""
Test module for rubber_engine.py
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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
import pytest

from fastoad.constants import FlightPhase
from fastoad.modules.propulsion.fuel_engine.rubber_engine import RubberEngine
from fastoad.utils.physics import Atmosphere


def test_compute_flight_points():
    engine = RubberEngine(5, 30, 1500, 1, 0.95, 10000)  # f0=1 so that output is simply fc/f0

    # Test with scalars
    sfc, thrust_rate, thrust = engine.compute_flight_points(0, 0, FlightPhase.TAKEOFF,
                                                            thrust_rate=0.8)  # with phase as FlightPhase
    np.testing.assert_allclose(thrust, 0.955 * 0.8, rtol=1e-2)
    np.testing.assert_allclose(sfc, 0.993e-5, rtol=1e-2)

    sfc, thrust_rate, thrust = engine.compute_flight_points(0.3, 0, FlightPhase.CLIMB.value,
                                                            thrust=0.357)  # with phase as int
    np.testing.assert_allclose(thrust_rate, 0.5, rtol=1e-2)
    np.testing.assert_allclose(sfc, 1.35e-5, rtol=1e-2)

    # Test full arrays
    # 2D arrays are used, where first line is for thrust rates, and second line
    # is for thrust values.
    # As thrust rates and thrust values match, thrust rate results are 2 equal
    # lines and so are thrust value results.
    machs = [0, 0.3, 0.3, 0.8, 0.8]
    altitudes = [0, 0, 0, 10000, 13000]
    thrust_rates = [0.8, 0.5, 0.5, 0.4, 0.7]
    thrusts = [0.955 * 0.8, 0.389, 0.357, 0.0967, 0.113]
    phases = [FlightPhase.TAKEOFF, FlightPhase.TAKEOFF,
              FlightPhase.CLIMB, FlightPhase.IDLE,
              FlightPhase.CRUISE.value]  # mix FlightPhase with integers
    expected_sfc = [0.993e-5, 1.35e-5, 1.35e-5, 1.84e-5, 1.60e-5]

    sfc, thrust_rate, thrust = engine.compute_flight_points([machs, machs],
                                                            [altitudes, altitudes],
                                                            [phases, phases],
                                                            [[True] * 5, [False] * 5],
                                                            [thrust_rates, [0] * 5],
                                                            [[0] * 5, thrusts])
    np.testing.assert_allclose(sfc, [expected_sfc, expected_sfc], rtol=1e-2)
    np.testing.assert_allclose(thrust_rate, [thrust_rates, thrust_rates], rtol=1e-2)
    np.testing.assert_allclose(thrust, [thrusts, thrusts], rtol=1e-2)

    # Test scalars + arrays 1
    machs = [0, 0.3, ]
    thrust_rates = [0.8, 0.5]
    expected_thrust = [0.955 * 0.8, 0.389]
    expected_sfc = [0.993e-5, 1.35e-5]

    sfc, _, thrust = engine.compute_flight_points(machs, 0, FlightPhase.TAKEOFF,
                                                  thrust_rate=thrust_rates)
    np.testing.assert_allclose(thrust, expected_thrust, rtol=1e-2)
    np.testing.assert_allclose(sfc, expected_sfc, rtol=1e-2)

    # Test scalars + arrays 2
    altitudes = [0, 0]
    phases = [FlightPhase.TAKEOFF.value, FlightPhase.CLIMB.value, ]
    expected_thrust = [0.389, 0.357]
    expected_sfc = [1.35e-5, 1.35e-5]

    sfc, _, thrust = engine.compute_flight_points(0.3, altitudes, phases, thrust_rate=0.5)
    np.testing.assert_allclose(thrust, expected_thrust, rtol=1e-2)
    np.testing.assert_allclose(sfc, expected_sfc, rtol=1e-2)


def test_installed_weight():
    fj44 = RubberEngine(0, 0, 0, 8452, 0, 0)
    np.testing.assert_allclose(fj44.installed_weight(), 225, rtol=1e-2)
    br710 = RubberEngine(0, 0, 0, 66034, 0, 0)
    np.testing.assert_allclose(br710.installed_weight(), 1756, rtol=1e-2)
    cfm56_3c1 = RubberEngine(0, 0, 0, 104533, 0, 0)
    np.testing.assert_allclose(cfm56_3c1.installed_weight(), 2542, rtol=1e-2)
    trent900 = RubberEngine(0, 0, 0, 340289, 0, 0)
    np.testing.assert_allclose(trent900.installed_weight(), 6519, rtol=1e-2)


def test_length():
    engine = RubberEngine(0, 0, 0, 75000, 0.95, 0)
    np.testing.assert_allclose(engine.length(), 2.73, rtol=1e-2)

    engine = RubberEngine(0, 0, 0, 250000, 0.92, 0)
    np.testing.assert_allclose(engine.length(), 4.39, rtol=1e-2)


def test_nacelle_diameter():
    engine = RubberEngine(3, 0, 0, 75000, 0, 0)
    np.testing.assert_allclose(engine.nacelle_diameter(), 1.61, rtol=1e-2)

    engine = RubberEngine(5.5, 0, 0, 250000, 0, 0)
    np.testing.assert_allclose(engine.nacelle_diameter(), 3.25, rtol=1e-2)


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
    ref_max_thrust_ratio = 0.949 * atm.density / 1.225 * (1 - 0.681 * machs + 0.511 * machs ** 2)
    np.testing.assert_allclose(max_thrust_ratio, ref_max_thrust_ratio, rtol=1e-2)

    # Check with Takeoff altitude
    atm = Atmosphere(0, altitude_in_feet=False)
    max_thrust_ratio = engine.max_thrust(atm, machs, 0)
    ref_max_thrust_ratio = 0.955 * atm.density / 1.225 * (1 - 0.730 * machs + 0.359 * machs ** 2)
    np.testing.assert_allclose(max_thrust_ratio, ref_max_thrust_ratio, rtol=1e-2)

    # Check Cruise above 11000 with compression rate != 30 and bypass ratio != 5
    engine = RubberEngine(4, 35, 1500, 1, 0, 0)  # f0=1 so that output is simply fmax/f0
    atm = Atmosphere(13000, altitude_in_feet=False)
    max_thrust_ratio = engine.max_thrust(atm, machs, -50)
    ref_max_thrust_ratio = 0.969 * atm.density / 1.225 * (1 - 0.636 * machs + 0.521 * machs ** 2)
    np.testing.assert_allclose(max_thrust_ratio, ref_max_thrust_ratio, rtol=1e-2)

    # Check with compression rate != 30 and bypass ratio != 5 and an array for altitudes (as
    # many values as mach numbers)
    engine = RubberEngine(6, 22, 1500, 1, 0, 0)  # f0=1 so that output is simply fmax/f0
    atm = Atmosphere(np.arange(3000, 13100, 1000), altitude_in_feet=False)
    max_thrust_ratio = engine.max_thrust(atm, machs, -50)
    ref_max_thrust_ratio = [0.698, 0.592, 0.501, 0.426, 0.364, 0.315,
                            0.277, 0.248, 0.228, 0.200, 0.178]
    np.testing.assert_allclose(max_thrust_ratio, ref_max_thrust_ratio, rtol=1e-2)


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
    np.testing.assert_allclose(sfc, [0.970e-5, 1.78e-5, 1.77e-5], rtol=1e-2)

    # Check with scalars
    trent900 = RubberEngine(7.14, 41, 0, 0, 0, 0)
    atm = Atmosphere(0, altitude_in_feet=False)
    sfc = trent900.sfc_at_max_thrust(atm, 0)
    np.testing.assert_allclose(sfc, 0.735e-5, rtol=1e-2)

    atm = Atmosphere(9144, altitude_in_feet=False)
    sfc = trent900.sfc_at_max_thrust(atm, 0.8)
    np.testing.assert_allclose(sfc, 1.68e-5, rtol=1e-2)  # value is different from PhD report

    # Check with arrays
    pw2037 = RubberEngine(6, 31.8, 0, 0, 0, 0)
    atm = Atmosphere(0, altitude_in_feet=False)
    sfc = pw2037.sfc_at_max_thrust(atm, 0)
    np.testing.assert_allclose(sfc, 0.906e-5, rtol=1e-2)

    atm = Atmosphere(10668, altitude_in_feet=False)
    sfc = pw2037.sfc_at_max_thrust(atm, 0.85)
    np.testing.assert_allclose(sfc, 1.74e-5, rtol=1e-2)  # value is different from PhD report


def test_sfc_ratio():
    """    Checks SFC ratio model    """
    design_alt = 10000
    engine = RubberEngine(0, 0, 0, 0, 0, design_alt)

    # Test values taken from method report (plots p. 80, see roux:2002 in refs.bib)
    # + values where original model fails (around dh=-1562.5)
    altitudes = design_alt + np.array([-2370, -1564, -1562.5, -1560, -846, 678, 2202, 3726])

    ratio = engine.sfc_ratio(altitudes, 0.8)
    assert ratio == pytest.approx([1.024, 1.020, 1.020, 1.020, 1.005, 0.977, 0.948, 0.918],
                                  rel=1e-3)
    ratio = engine.sfc_ratio(altitudes, 0.6)
    assert ratio == pytest.approx([1.074, 1.080, 1.080, 1.080, 1.044, 0.994, 0.935, 0.877],
                                  rel=1e-3)
    assert engine.sfc_ratio(altitudes, 1.0) == pytest.approx(1.0, rel=1e-3)

    # Because there some code differs when we have scalars:
    assert engine.sfc_ratio(design_alt - 1562.5, 0.6) == pytest.approx(1.080, rel=1e-3)
