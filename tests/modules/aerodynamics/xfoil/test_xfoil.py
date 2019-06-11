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
XFOIL_RESULT = os.path.join(os.path.dirname(__file__), 'tmp', 'xfoil_result.txt')  # make
INPUT_PROFILE = os.path.join(os.path.dirname(__file__), 'data', 'BACJ-new.txt')


@pytest.fixture(scope='module')
def xfoil():
    # Setup
    xfoil = Xfoil()
    xfoil.options['xfoil_dir'] = XFOIL_DIR
    xfoil.options['input_profile'] = INPUT_PROFILE
    xfoil.options['xfoil_result'] = XFOIL_RESULT
    xfoil.setup()

    return xfoil


def test_compute(xfoil):
    inputs = {'xfoil:reynolds': 18000000,
              'xfoil:mach': 0.20,
              'geometry:wing_sweep_25': 25.,
              }
    outputs = {}
    xfoil.compute(inputs, outputs)
    assert xfoil.get_max_cl() == 1.9408
