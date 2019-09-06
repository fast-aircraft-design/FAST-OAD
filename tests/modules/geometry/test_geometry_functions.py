"""
Test module for geometry general functions
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

# pylint: disable=redefined-outer-name  # needed for pytest fixtures
import os

from tests.testing_utilities import compare_text_files

from fastoad.modules.geometry.functions.airfoil_reshape import airfoil_reshape

def test_reshape_airfoil():
    """ Tests the reshape of the airfoil """

    f_path_data = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')
    f_path_ori = os.path.join(f_path_data, 'BACJ.txt')
    f_path_root_ref = os.path.join(f_path_data, 'root_ref.txt')
    f_path_root = os.path.join(f_path_data, 'root.txt')
    el_emp = 0.159

    airfoil_reshape(el_emp, f_path_ori, f_path_root)

    are_same = compare_text_files(f_path_root_ref, f_path_root)

    assert are_same
