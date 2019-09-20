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

from fastoad.modules.propulsion.fuel_engine.rubber_engine import RubberEngine
from fastoad.utils.physics import Atmosphere


def test_compute_manual():
    engine = RubberEngine(5, 30, 1500, -50, -100, 1, 0.95,
                          15000)  # f0=1 so that output is simply fc/f0
    fc, sfc = engine.compute_manual(0, 0, 0.8, 'MTO')
    np.testing.assert_allclose(fc, 0.955 * 0.8, rtol=1e-2)
    np.testing.assert_allclose(sfc, 0.993e-5, rtol=1e-2)

    fc, sfc = engine.compute_manual(0.3, 0, 0.5, 'MTO')
    np.testing.assert_allclose(fc, 0.389, rtol=1e-2)
    np.testing.assert_allclose(sfc, 1.35e-5, rtol=1e-2)

    fc, sfc = engine.compute_manual(0.3, 0, 0.5, 'CLIMB')
    np.testing.assert_allclose(fc, 0.357, rtol=1e-2)
    np.testing.assert_allclose(sfc, 1.35e-5, rtol=1e-2)

    fc, sfc = engine.compute_manual(0.8, 10000, 0.4, 'FI')
    np.testing.assert_allclose(fc, 0.152, rtol=1e-2)
    np.testing.assert_allclose(sfc, 1.90e-5, rtol=1e-2)

    fc, sfc = engine.compute_manual(0.8, 13000, 0.4, 'FI')
    np.testing.assert_allclose(fc, 0.146, rtol=1e-2)
    np.testing.assert_allclose(sfc, 1.90e-5, rtol=1e-2)


def test_compute_regulated():
    engine = RubberEngine(5, 30, 1500, -50, -100, 1, 0.95,
                          15000)  # f0=1 so that input drag in drag/f0
    sfc, thrust_rate = engine.compute_regulated(0, 0, 0.955 * 0.8, 'MTO')
    np.testing.assert_allclose(thrust_rate, 0.8, rtol=1e-2)
    np.testing.assert_allclose(sfc, 0.993e-5, rtol=1e-2)

    sfc, thrust_rate = engine.compute_regulated(0.3, 0, 0.389, 'MTO')
    np.testing.assert_allclose(thrust_rate, 0.5, rtol=1e-2)
    np.testing.assert_allclose(sfc, 1.35e-5, rtol=1e-2)

    sfc, thrust_rate = engine.compute_regulated(0.3, 0, 0.357, 'CLIMB')
    np.testing.assert_allclose(thrust_rate, 0.5, rtol=1e-2)
    np.testing.assert_allclose(sfc, 1.35e-5, rtol=1e-2)

    sfc, thrust_rate = engine.compute_regulated(0.8, 10000, 0.152, 'FI')
    np.testing.assert_allclose(thrust_rate, 0.4, rtol=1e-2)
    np.testing.assert_allclose(sfc, 1.90e-5, rtol=1e-2)

    sfc, thrust_rate = engine.compute_regulated(0.8, 13000, 0.146, 'FI')
    np.testing.assert_allclose(thrust_rate, 0.4, rtol=1e-2)
    np.testing.assert_allclose(sfc, 1.90e-5, rtol=1e-2)


def test_installed_weight():
    fj44 = RubberEngine(0, 0, 0, 0, 0, 8452, 0, 0)
    np.testing.assert_allclose(fj44.installed_weight(), 225, rtol=1e-2)
    br710 = RubberEngine(0, 0, 0, 0, 0, 66034, 0, 0)
    np.testing.assert_allclose(br710.installed_weight(), 1756, rtol=1e-2)
    cfm56_3c1 = RubberEngine(0, 0, 0, 0, 0, 104533, 0, 0)
    np.testing.assert_allclose(cfm56_3c1.installed_weight(), 2542, rtol=1e-2)
    trent900 = RubberEngine(0, 0, 0, 0, 0, 340289, 0, 0)
    np.testing.assert_allclose(trent900.installed_weight(), 6519, rtol=1e-2)


def test_length():
    engine = RubberEngine(0, 0, 0, 0, 0, 75000, 0.95, 0)
    np.testing.assert_allclose(engine.length(), 2.73, rtol=1e-2)

    engine = RubberEngine(0, 0, 0, 0, 0, 250000, 0.92, 0)
    np.testing.assert_allclose(engine.length(), 4.39, rtol=1e-2)


def test_nacelle_diameter():
    engine = RubberEngine(3, 0, 0, 0, 0, 75000, 0, 0)
    np.testing.assert_allclose(engine.nacelle_diameter(), 1.61, rtol=1e-2)

    engine = RubberEngine(5.5, 0, 0, 0, 0, 250000, 0, 0)
    np.testing.assert_allclose(engine.nacelle_diameter(), 3.25, rtol=1e-2)


def test_max_thrust():
    engine = RubberEngine(5, 30, 1500, 0, 0, 10, 0, 0)  # f0=10 so that output is simply fmax/f0
    machs = np.arange(0, 1.01, 0.1)

    # Check against simplified (but analytically equivalent) formulas
    # As in p 59. of Roux PhD report, but with correct coefficients (yes, those in report
    # are not consistent with the complete formula nor the figure 2.19 just below.

    # Check cruise
    atm = Atmosphere(11000, altitude_in_feet=False)
    max_thrust_ratio = engine.max_thrust(atm, machs, -100)
    ref_max_thrust_ratio = 0.949 * atm.density / 1.225 * (
            1 - 0.681 * machs + 0.511 * machs ** 2)
    np.testing.assert_allclose(max_thrust_ratio, ref_max_thrust_ratio, rtol=1e-2)

    # Check Take-off
    atm = Atmosphere(0, altitude_in_feet=False)
    max_thrust_ratio = engine.max_thrust(atm, machs, 0)
    ref_max_thrust_ratio = 0.955 * atm.density / 1.225 * (
            1 - 0.730 * machs + 0.359 * machs ** 2)
    np.testing.assert_allclose(max_thrust_ratio, ref_max_thrust_ratio, rtol=1e-2)

    # Check Cruise with compression rate != 30 and bypass ratio != 5
    engine = RubberEngine(4, 35, 1500, 0, 0, 10, 0, 0)  # f0=10 so that output is simply fmax/f0
    atm = Atmosphere(13000, altitude_in_feet=False)
    max_thrust_ratio = engine.max_thrust(atm, machs, -50)
    ref_max_thrust_ratio = 0.969 * atm.density / 1.225 * (
            1 - 0.636 * machs + 0.521 * machs ** 2)
    np.testing.assert_allclose(max_thrust_ratio, ref_max_thrust_ratio, rtol=1e-2)


def test__sfc_calc_at_max_thrust():
    cfm56_3c1 = RubberEngine(6, 25.7, 0, 0, 0, 0, 0, 0)

    cfm56_3c1.altitude = 0
    cfm56_3c1.mach = 0
    cfm56_3c1.temperature, cfm56_3c1.density, _, _ = cfm56_3c1._atmosphere(cfm56_3c1.altitude)
    sfc = cfm56_3c1._sfc_calc_at_max_thrust()
    np.testing.assert_allclose(sfc, 0.970e-5, rtol=1e-2)

    cfm56_3c1.altitude = 10668
    cfm56_3c1.mach = 0.8
    cfm56_3c1.temperature, cfm56_3c1.density, _, _ = cfm56_3c1._atmosphere(cfm56_3c1.altitude)
    sfc = cfm56_3c1._sfc_calc_at_max_thrust()
    np.testing.assert_allclose(sfc, 1.78e-5, rtol=1e-2)  # value is different from PhD report

    cfm56_3c1.altitude = 13000  # for testing above 11000, though no ref value in PhD report
    cfm56_3c1.mach = 0.8
    cfm56_3c1.temperature, cfm56_3c1.density, _, _ = cfm56_3c1._atmosphere(cfm56_3c1.altitude)
    sfc = cfm56_3c1._sfc_calc_at_max_thrust()
    np.testing.assert_allclose(sfc, 1.77e-5, rtol=1e-2)  # value is different from PhD report

    trent900 = RubberEngine(7.14, 41, 0, 0, 0, 0, 0, 0)
    trent900.altitude = 0
    trent900.mach = 0
    trent900.temperature, trent900.density, _, _ = trent900._atmosphere(trent900.altitude)
    sfc = trent900._sfc_calc_at_max_thrust()
    np.testing.assert_allclose(sfc, 0.735e-5, rtol=1e-2)

    trent900.altitude = 9144
    trent900.mach = 0.8
    trent900.temperature, trent900.density, _, _ = trent900._atmosphere(trent900.altitude)
    sfc = trent900._sfc_calc_at_max_thrust()
    np.testing.assert_allclose(sfc, 1.68e-5, rtol=1e-2)  # value is different from PhD report

    pw2037 = RubberEngine(6, 31.8, 0, 0, 0, 0, 0, 0)
    pw2037.altitude = 0
    pw2037.mach = 0
    pw2037.temperature, pw2037.density, _, _ = pw2037._atmosphere(pw2037.altitude)
    sfc = pw2037._sfc_calc_at_max_thrust()
    np.testing.assert_allclose(sfc, 0.906e-5, rtol=1e-2)

    pw2037.altitude = 10668
    pw2037.mach = 0.85
    pw2037.temperature, pw2037.density, _, _ = pw2037._atmosphere(pw2037.altitude)
    sfc = pw2037._sfc_calc_at_max_thrust()
    np.testing.assert_allclose(sfc, 1.74e-5, rtol=1e-2)  # value is different from PhD report
