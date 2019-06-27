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
import os.path as pth

import numpy as np
import pytest
from openmdao.core.problem import Problem

from fastoad.io.xml.openmdao_basic_io import OpenMdaoXmlIO
from fastoad.modules.aerodynamics.external import OpenVSP
from tests.conftest import root_folder

OPENVSP_DIR = pth.join(root_folder, 'OpenVSP-3.5.1-win32')
OPENVSP_RESULTS = pth.join(pth.dirname(__file__), 'results')
INPUT_FILE = pth.join(pth.dirname(__file__), 'data', 'inputs.xml')
TMP_DIR = pth.join(pth.dirname(__file__), 'tmp')


def get_OpenVSP():
    openvsp = OpenVSP()
    openvsp.options['ovsp_dir'] = OPENVSP_DIR
    openvsp.options['result_dir'] = OPENVSP_RESULTS
    openvsp.options['tmp_dir'] = TMP_DIR

    os.makedirs(OPENVSP_RESULTS, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)
    return openvsp


@pytest.fixture(scope="module")
def indep_vars():
    reader = OpenMdaoXmlIO(INPUT_FILE)
    reader.path_separator = ':'
    ivc = reader.read()
    return ivc


def test_run_openmdao(indep_vars):
    indep_vars.add_output('AoA_min', 0.)
    indep_vars.add_output('AoA_max', 2.5)
    indep_vars.add_output('AoA_step', 0.5)
    indep_vars.add_output('openvsp:mach', 0.2)
    indep_vars.add_output('openvsp:altitude', 0)

    openvsp_computation = Problem()
    model = openvsp_computation.model
    model.add_subsystem('design_variables', indep_vars, promotes=['*'])
    model.add_subsystem('openvsp', get_OpenVSP(), promotes=['*'])

    openvsp_computation.setup(mode='fwd')
    openvsp_computation.run_model()

    assert pth.exists(pth.join(TMP_DIR, OpenVSP.vspscript_filename))
    # os.remove(pth.join(TMP_DIR, OpenVSP.vspscript_filename))

    assert pth.exists(pth.join(TMP_DIR, OpenVSP.result_filename))

    results = np.genfromtxt(os.path.join(TMP_DIR, OpenVSP.result_filename), delimiter=',')
    CL = results[:, 0]
    CDi = results[:, 1]
    CDtot = results[:, 2]

    # Result depends marginally on number of used cpu count. So tolerance is set to 0.5 lift count
    # and 0.5 drag count
    # TODO: fix VSPAero computation and put correct values in assert
    assert CL == pytest.approx([0.04901, 0.05909, 0.06918, 0.07926], abs=0.005)
    assert CDi == pytest.approx([1.2e-04, 1.7e-04, 2.2e-04, 2.9e-04], abs=0.00005)
    assert CDtot == pytest.approx(0.00804, abs=0.00005)

    # shutil.rmtree(TMP_DIR)
