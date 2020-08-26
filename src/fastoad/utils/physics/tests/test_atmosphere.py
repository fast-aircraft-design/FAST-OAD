"""Tests for Atmosphere class"""
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

from numbers import Number

import numpy as np
import pytest
from numpy.testing import assert_allclose
from scipy.constants import foot

from ..atmosphere import Atmosphere


def test_atmosphere():
    """Tests properties of Atmosphere class."""
    # Altitudes in meters Values at disa=0 from "Advanced Aircraft Design (
    # Egbert TORENBEEK, Oxford, UK: John Wiley & Sons Ltd, 2013) Appendix B,
    # p.397-398" Values at disa=10 from
    # https://www.digitaldutch.com/atmoscalc/, with a 0.98749 factor on
    # viscosity because at sea level and disa=0, the calculator gives
    # 1.81206e-5 for dynamic viscosity, though ISA assumption is 1.7894e-5
    expectations = np.array(
        [
            (0, 0, 288.15, 1.225, 101325, 1.460e-05, 340.29),
            (500, 0, 284.90, 1.1673, 95461, 1.519e-05, 338.37),
            (1000, 0, 281.65, 1.1117, 89874, 1.581e-05, 336.43),
            (1500, 0, 278.40, 1.0581, 84556, 1.646e-05, 334.49),
            (2000, 0, 275.15, 1.0065, 79495, 1.714e-05, 332.53),
            (2500, 0, 271.90, 0.9569, 74682, 1.787e-05, 330.56),
            (3000, 0, 268.65, 0.9091, 70108, 1.863e-05, 328.58),
            (3500, 0, 265.40, 0.8632, 65764, 1.943e-05, 326.58),
            (4000, 0, 262.15, 0.8191, 61640, 2.028e-05, 324.58),
            (4500, 0, 258.90, 0.7768, 57728, 2.117e-05, 322.56),
            (5000, 0, 255.65, 0.7361, 54020, 2.211e-05, 320.53),
            (5500, 0, 252.40, 0.6971, 50506, 2.311e-05, 318.48),
            (6000, 0, 249.15, 0.6597, 47181, 2.417e-05, 316.43),
            (6500, 0, 245.90, 0.6238, 44034, 2.529e-05, 314.36),
            (7000, 0, 242.65, 0.5895, 41060, 2.648e-05, 312.27),
            (7500, 0, 239.40, 0.5566, 38251, 2.773e-05, 310.17),
            (8000, 0, 236.15, 0.5252, 35599, 2.906e-05, 308.06),
            (8500, 0, 232.90, 0.4951, 33099, 3.048e-05, 305.93),
            (9000, 0, 229.65, 0.4663, 30742, 3.199e-05, 303.79),
            (9500, 0, 226.40, 0.4389, 28523, 3.359e-05, 301.63),
            (10000, 0, 223.15, 0.4127, 26436, 3.530e-05, 299.46),
            (10500, 0, 219.90, 0.3877, 24474, 3.712e-05, 297.27),
            (11000, 0, 216.65, 0.3639, 22632, 3.905e-05, 295.07),
            (12000, 0, 216.65, 0.3108, 19330, 4.573e-05, 295.07),
            (13000, 0, 216.65, 0.2655, 16510, 5.353e-05, 295.07),
            (14000, 0, 216.65, 0.2268, 14101, 6.266e-05, 295.07),
            (15000, 0, 216.65, 0.1937, 12044, 7.337e-05, 295.07),
            (16000, 0, 216.65, 0.1654, 10287, 8.592e-05, 295.07),
            (17000, 0, 216.65, 0.1413, 8786, 1.006e-04, 295.07),
            (18000, 0, 216.65, 0.1207, 7505, 1.177e-04, 295.07),
            (19000, 0, 216.65, 0.1031, 6410, 1.378e-04, 295.07),
            (20000, 0, 216.65, 0.088, 5475, 1.615e-04, 295.07),
            (0, 10, 298.15, 1.1839, 101325, 1.5527e-5, 346.15),
            (1000, 10, 291.65, 1.0735, 89875, 1.6829e-5, 342.36),
            (3000, 10, 278.65, 0.87650, 70108, 1.9877e-5, 334.64),
            (10000, 10, 233.15, 0.39500, 26436, 3.8106e-05, 306.10),
            (14000, 10, 226.65, 0.2167, 14102, 6.7808e-05, 301.80),
        ],
        dtype=[
            ("alt", "f8"),
            ("dT", "f4"),
            ("T", "f4"),
            ("rho", "f4"),
            ("P", "f4"),
            ("visc", "f4"),
            ("SoS", "f4"),
        ],
    )

    for values in expectations:
        # Checking with altitude provided as scalar
        alt = values["alt"] / foot
        assert isinstance(alt, Number)
        atm = Atmosphere(alt, values["dT"])
        assert values["T"] == pytest.approx(atm.temperature, rel=1e-4)
        assert values["rho"] == pytest.approx(atm.density, rel=1e-3)
        assert values["P"] == pytest.approx(atm.pressure, rel=1e-4)
        assert values["visc"] == pytest.approx(atm.kinematic_viscosity, rel=1e-2)
        assert values["SoS"] == pytest.approx(atm.speed_of_sound, rel=1e-3)

        # Checking with altitude provided as one-element list
        alt = [values["alt"] / foot]
        assert isinstance(alt, list)
        atm = Atmosphere(alt, values["dT"])
        assert values["T"] == pytest.approx(atm.temperature, rel=1e-4)
        assert values["rho"] == pytest.approx(atm.density, rel=1e-3)
        assert values["P"] == pytest.approx(atm.pressure, rel=1e-4)
        assert values["visc"] == pytest.approx(atm.kinematic_viscosity, rel=1e-2)
        assert values["SoS"] == pytest.approx(atm.speed_of_sound, rel=1e-3)

    for delta_t in [0, 10]:
        idx = expectations["dT"] == delta_t

        # Checking with altitude provided as 1D numpy array
        alt = expectations["alt"][idx] / foot
        assert isinstance(alt, np.ndarray)
        assert len(alt.shape) == 1
        atm = Atmosphere(alt, delta_t)
        assert expectations["T"][idx] == pytest.approx(atm.temperature, rel=1e-4)
        assert expectations["rho"][idx] == pytest.approx(atm.density, rel=1e-3)
        assert expectations["P"][idx] == pytest.approx(atm.pressure, rel=1e-4)
        assert expectations["visc"][idx] == pytest.approx(atm.kinematic_viscosity, rel=1e-2)
        assert expectations["SoS"][idx] == pytest.approx(atm.speed_of_sound, rel=1e-3)
        # Additional check for get_altitude in meters
        assert expectations["alt"][idx] == pytest.approx(
            atm.get_altitude(altitude_in_feet=False), rel=1e-3
        )

        # Checking with altitude provided as a list and in meters
        alt = expectations["alt"][idx].tolist()
        assert isinstance(alt, list)
        atm = Atmosphere(alt, delta_t, altitude_in_feet=False)
        assert expectations["T"][idx] == pytest.approx(atm.temperature, rel=1e-4)
        assert expectations["rho"][idx] == pytest.approx(atm.density, rel=1e-3)
        assert expectations["P"][idx] == pytest.approx(atm.pressure, rel=1e-4)
        assert expectations["visc"][idx] == pytest.approx(atm.kinematic_viscosity, rel=1e-2)
        assert expectations["SoS"][idx] == pytest.approx(atm.speed_of_sound, rel=1e-3)
        # Additional check for get_altitude in feet
        assert expectations["alt"][idx] / foot == pytest.approx(atm.get_altitude(), rel=1e-3)


def test_reynolds():
    """Tests computation of Reynolds number."""
    atm = Atmosphere([[0, 35000], [0, 35000]])
    mach = [[0.2, 0.2], [0.8, 0.8]]

    # source:  http://www.aerospaceweb.org/design/scripts/atmosphere/
    expected_reynolds = [[4.6593e6, 1.5738e6], [1.8637e7, 6.2952e6]]

    assert_allclose(atm.get_unitary_reynolds(mach), expected_reynolds, rtol=3e-3)


def test_speed_conversions():
    """Tests for speed conversions."""
    atm = Atmosphere([[0.0, 1000.0, 35000.0], [0.0, 1000.0, 35000.0]])
    TAS = [[100.0, 100.0, 100.0], [200.0, 200.0, 200.0]]

    # source:  http://www.aerospaceweb.org/design/scripts/atmosphere/
    expected_EAS = [[100.0, 98.5427, 55.7293], [200.0, 197.0853, 111.4586]]

    assert_allclose(atm.get_equivalent_airspeed(TAS), expected_EAS, rtol=3e-3)

    assert_allclose(atm.get_true_airspeed(expected_EAS), TAS, rtol=3e-3)
