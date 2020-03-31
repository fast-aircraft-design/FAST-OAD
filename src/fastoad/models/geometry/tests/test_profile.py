""" Test module for profile.py """
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
import pytest
from numpy.testing import assert_allclose

# pylint: disable=redefined-outer-name  # false positive on pytest fixtures
from ..profiles.profile import Profile


@pytest.fixture()
def point_set():
    """ Defines a test profile """
    return np.array(
        [
            [1, 0.00095],
            [0.99, 0.00315],
            [0.979999, 0.00534],
            [0.969999, 0.007521],
            [0.95, 0.01183],
            [0.929999, 0.01602],
            [0.9, 0.02199],
            [0.859999, 0.02919],
            [0.819999, 0.03543],
            [0.78, 0.040691],
            [0.74, 0.045011],
            [0.7, 0.048471],
            [0.649999, 0.05179],
            [0.599999, 0.05413],
            [0.549999, 0.05562],
            [0.499999, 0.056341],
            [0.449999, 0.05632],
            [0.400001, 0.05562],
            [0.350001, 0.054261],
            [0.3, 0.052311],
            [0.26, 0.0503],
            [0.22, 0.04788],
            [0.190001, 0.04576],
            [0.16, 0.04322],
            [0.140001, 0.041211],
            [0.12, 0.03888],
            [0.1, 0.03617],
            [0.080001, 0.03304],
            [0.069999, 0.03129],
            [0.06, 0.0294],
            [0.05, 0.027351],
            [0.04, 0.02508],
            [0.032001, 0.02305],
            [0.026001, 0.02136],
            [0.019999, 0.01946],
            [0.014, 0.01717],
            [0.012, 0.01624],
            [0.01, 0.015191],
            [0.008, 0.01398],
            [0.006, 0.01251],
            [0.005001, 0.01163],
            [0.004, 0.01061],
            [0.003001, 0.00939],
            [0.002, 0.00782],
            [0.001399, 0.00657],
            [0.000801, 0.005001],
            [0.0004, 0.00359],
            [0.0002, 0.0026],
            [0.000101, 0.00168],
            [0, 0],
            [0.000101, -0.00162],
            [0.0002, -0.0025],
            [0.0004, -0.00354],
            [0.000801, -0.004949],
            [0.001399, -0.00649],
            [0.002, -0.00771],
            [0.003001, -0.00935],
            [0.004, -0.010619],
            [0.005001, -0.011799],
            [0.006, -0.012779],
            [0.008, -0.0144],
            [0.01, -0.015759],
            [0.012, -0.01688],
            [0.014, -0.018009],
            [0.019999, -0.020779],
            [0.026001, -0.02296],
            [0.032001, -0.02491],
            [0.04, -0.027149],
            [0.05, -0.02954],
            [0.06, -0.031589],
            [0.069999, -0.03335],
            [0.080001, -0.034889],
            [0.1, -0.03739],
            [0.12, -0.039299],
            [0.140001, -0.04082],
            [0.16, -0.04201],
            [0.190001, -0.043409],
            [0.22, -0.04445],
            [0.26, -0.0454],
            [0.3, -0.04581],
            [0.350001, -0.04588],
            [0.400001, -0.045079],
            [0.449999, -0.043379],
            [0.499999, -0.04059],
            [0.549999, -0.03659],
            [0.599999, -0.031309],
            [0.649999, -0.024899],
            [0.7, -0.017679],
            [0.74, -0.01196],
            [0.78, -0.006139],
            [0.819999, -0.001319],
            [0.859999, 0.002141],
            [0.9, 0.00388],
            [0.929999, 0.003941],
            [0.95, 0.00334],
            [0.969999, 0.00224],
            [0.979999, 0.001491],
            [0.99, 0.00061],
            [1, 0.00095],
        ]
    )


def test_set_points(point_set):
    """ test of Profile.set_points() """

    x = point_set[:, 0]  # pylint:disable=invalid-name
    z = point_set[:, 1]  # pylint:disable=invalid-name

    # Direct initialization from point set
    profile = Profile()
    profile.set_points(x * 2.5, z * 2.5)
    assert_allclose(2.5, profile.chord_length, rtol=1e-4)
    assert_allclose(0.10070, profile.thickness_ratio, rtol=1e-4)

    # Initialization after having set chord length
    profile = Profile()
    profile.chord_length = 0.5
    profile.set_points(x, z)
    assert_allclose(0.5, profile.chord_length, rtol=1e-4)
    assert_allclose(0.10070, profile.thickness_ratio, rtol=1e-4)

    # Initialization after having set relative thickness
    profile = Profile()
    profile.thickness_ratio = 0.2
    profile.set_points(x * 1.5, z)
    assert_allclose(1.5, profile.chord_length, rtol=1e-4)
    assert_allclose(0.2, profile.thickness_ratio, rtol=1e-4)

    # Setting points while explicitly ignoring previous chord length and thickness
    profile.set_points(x, z, False, False)
    assert_allclose(1.0, profile.chord_length, rtol=1e-4)
    assert_allclose(0.10070, profile.thickness_ratio, rtol=1e-4)

    # Check relative thickness distribution
    relative_thickness = profile.get_relative_thickness()
    assert_allclose(0.0, np.min(relative_thickness["x"]), rtol=1e-4)
    assert_allclose(1.0, np.max(relative_thickness["x"]), rtol=1e-4)
    assert_allclose(0.10070, np.max(relative_thickness["thickness"]), rtol=1e-4)

    # import matplotlib.pyplot as plt
    # plt.axes(aspect='equal')
    # plt.plot(profile.get_upper_side()['x'], profile.get_upper_side()['z'], 'o-')
    # plt.plot(profile.get_lower_side()['x'], profile.get_lower_side()['z'], 'o-')
    # plt.plot(profile.get_mean_line()['x'], profile.get_mean_line()['z'], 'o-')
    # plt.show()
