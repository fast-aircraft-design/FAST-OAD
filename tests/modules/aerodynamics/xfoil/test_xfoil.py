"""
Test module for XFOIL component
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

# pylint: disable=redefined-outer-name  # needed for fixtures

import os.path as pth
import shutil

import pytest

from fastoad.modules.aerodynamics.xfoil import XfoilPolar, XfoilPoint
from tests.conftest import root_folder

XFOIL_EXE = pth.join(root_folder, 'XFOIL', 'xfoil.exe')
XFOIL_RESULTS = pth.join(pth.dirname(__file__), 'results')
INPUT_PROFILE = pth.join(pth.dirname(__file__), 'data', 'BACJ-new.txt')


def test_polar_compute():
    """ Tests a simple XFOIL run"""

    xfoil = XfoilPolar()
    xfoil.options['xfoil_exe_path'] = XFOIL_EXE
    xfoil.options['profile_path'] = INPUT_PROFILE
    xfoil.setup()

    if pth.exists(XFOIL_RESULTS):
        shutil.rmtree(XFOIL_RESULTS)
    inputs = {'profile:reynolds': 18000000,
              'profile:mach': 0.20,
              'geometry:wing_sweep_25': 25.,
              }
    outputs = {}
    xfoil.compute(inputs, outputs)
    assert outputs['aerodynamics:Cl_max_2D'] == pytest.approx(1.9408, 1e-4)
    assert outputs['aerodynamics:Cl_max_clean'] == pytest.approx(1.5831, 1e-4)
    assert not pth.exists(XFOIL_RESULTS)

    xfoil.options['result_folder_path'] = pth.join(XFOIL_RESULTS, 'polar')
    outputs = {}
    xfoil.compute(inputs, outputs)
    assert outputs['aerodynamics:Cl_max_2D'] == pytest.approx(1.9408, 1e-4)
    assert outputs['aerodynamics:Cl_max_clean'] == pytest.approx(1.5831, 1e-4)
    assert pth.exists(XFOIL_RESULTS)
    assert pth.exists(pth.join(XFOIL_RESULTS, 'polar', 'result.txt'))


def test_point_compute():
    """ Tests a simple XFOIL run"""

    xfoil = XfoilPoint()
    xfoil.options['xfoil_exe_path'] = XFOIL_EXE
    xfoil.options['profile_path'] = INPUT_PROFILE
    xfoil.options['result_folder_path'] = pth.join(XFOIL_RESULTS, 'point')
    xfoil.setup()

    inputs = {'profile:reynolds': 18000000,
              'profile:mach': 0.20,
              'profile:alpha': 1.,
              }
    outputs = {}
    xfoil.compute(inputs, outputs)
    assert outputs['xfoil:CL'] == pytest.approx(0.3870, 1e-4)
