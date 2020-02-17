"""
Test module for geometry general functions
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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

import os.path as pth

import numpy as np
from numpy.testing import assert_allclose

from fastoad.modules.geometry.functions.airfoil_reshape import get_profile

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), 'data')
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__),
                               'results', pth.splitext(pth.basename(__file__))[0])


def test_get_profile():
    """ non-regression test for changing the relative thickness of a profile """
    # Read the expected result
    ref_profile = np.genfromtxt(pth.join(DATA_FOLDER_PATH, 'root_ref.txt'),
                                skip_header=1, delimiter='\t')

    profile = get_profile('BACJ.txt', relative_thickness=0.159)
    assert_allclose(profile, ref_profile, rtol=1e-10)
