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

# pylint: disable=redefined-outer-name  # needed for pytest fixtures
import filecmp
import os
import os.path as pth
from shutil import rmtree

import pytest

from fastoad.modules.geometry.functions import airfoil_reshape

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), 'data')
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__),
                               'results', pth.splitext(pth.basename(__file__))[0])


@pytest.fixture(scope='module')
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_reshape_airfoil():
    """ Tests the reshape of the airfoil """

    os.makedirs(RESULTS_FOLDER_PATH)

    f_path_ori = os.path.join(DATA_FOLDER_PATH, 'BACJ.txt')
    f_path_root_ref = os.path.join(DATA_FOLDER_PATH, 'root_ref.txt')
    f_path_root = os.path.join(RESULTS_FOLDER_PATH, 'root.txt')
    el_emp = 0.159

    airfoil_reshape(el_emp, f_path_ori, f_path_root)

    are_same = filecmp.cmp(f_path_root_ref, f_path_root)

    assert are_same
