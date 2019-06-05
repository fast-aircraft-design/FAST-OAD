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
import os

import pytest

from fastoad.modules.aerodynamics.xfoil import Xfoil
from tests.conftest import root_folder

XFOIL_DIR = os.path.join(root_folder, 'XFOIL')
TMP_DIR = os.path.join(root_folder, 'tmp')
RESOURCE_DIR = os.path.join(os.path.dirname(__file__), 'resources')


@pytest.fixture(scope='module')
def xfoil():
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    xfoil = Xfoil()
    xfoil.options['xfoil_dir'] = XFOIL_DIR
    xfoil.options['tmp_dir'] = TMP_DIR
    xfoil.options['resources_dir'] = RESOURCE_DIR
    xfoil.options['xfoil_result'] = os.path.join(TMP_DIR, 'xfoil_result.txt')

    _cleanup_xfoil_files()  # remove if any
    xfoil.setup()
    yield xfoil

    try:
        _cleanup_xfoil_files()
        os.rmdir(TMP_DIR)
    except OSError:
        pass


def _cleanup_xfoil_files():
    try:
        for f in [Xfoil.xfoil_script_filename, Xfoil.xfoil_cmd,
                  Xfoil.xfoil_result_filename, Xfoil.xfoil_bacj_new]:
            fpath = os.path.join(TMP_DIR, f)
            if os.path.exists(fpath):
                os.remove(fpath)
    except OSError:
        pass


def test_successful_run(xfoil):
    inputs = {'geometry:wing_toc_aero': 0.12840,
              'xfoil:reynolds': 18000000,
              'xfoil:mach': 0.20,
              'geometry:wing_sweep_25': 25.,
              }
    outputs = {}
    xfoil.compute(inputs, outputs)
    assert xfoil.get_max_cl() == 1.9408
