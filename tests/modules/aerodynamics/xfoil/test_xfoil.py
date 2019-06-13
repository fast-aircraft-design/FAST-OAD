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
from openmdao.components.exec_comp import ExecComp
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.problem import Problem
from openmdao.drivers.scipy_optimizer import ScipyOptimizeDriver

from fastoad.modules.aerodynamics.xfoil import XfoilPolar, XfoilPoint
from tests.conftest import root_folder

XFOIL_EXE = pth.join(root_folder, 'XFOIL', 'xfoil.exe')
XFOIL_RESULTS = pth.join(pth.dirname(__file__), 'results')
INPUT_PROFILE = pth.join(pth.dirname(__file__), 'data', 'BACJ-new.txt')


def test_cl_max_from_polar():
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
    # assert outputs['aerodynamics:Cl_max_2D'] == pytest.approx(1.9408, 1e-4)
    # assert outputs['aerodynamics:Cl_max_clean'] == pytest.approx(1.5831, 1e-4)
    assert not pth.exists(XFOIL_RESULTS)

    xfoil.options['result_folder_path'] = pth.join(XFOIL_RESULTS, 'polar')
    outputs = {}
    xfoil.compute(inputs, outputs)
    assert outputs['aerodynamics:Cl_max_2D'] == pytest.approx(1.9408, 1e-4)
    assert outputs['aerodynamics:Cl_max_clean'] == pytest.approx(1.5831, 1e-4)
    assert pth.exists(XFOIL_RESULTS)
    assert pth.exists(pth.join(XFOIL_RESULTS, 'polar', 'result.txt'))


# @pytest.mark.skip('XFOIL gives different results than with complete polar.')
# TODO: try and figure out how to make things consistent
def test_point_compute():
    """ Tests a single alpha XFOIL run"""

    xfoil = XfoilPoint()
    xfoil.options['xfoil_exe_path'] = XFOIL_EXE
    xfoil.options['profile_path'] = INPUT_PROFILE
    xfoil.setup()

    # Same result as in polar
    inputs = {'profile:reynolds': 18000000, 'profile:mach': 0.20, 'profile:alpha': 20.}
    outputs = {}
    xfoil.compute(inputs, outputs)
    assert outputs['xfoil:CL'] == pytest.approx(1.9226, 1e-4)

    # XFOIL computation fails
    inputs['profile:alpha'] = 21.
    outputs = {}
    xfoil.compute(inputs, outputs)
    assert 'xfoil:CL' not in outputs

    # Same result as in polar (identified maximum)
    inputs['profile:alpha'] = 21.5
    outputs = {}
    xfoil.compute(inputs, outputs)
    assert outputs['xfoil:CL'] == pytest.approx(1.9408, 1e-4)

    # AoA = 20.28°: larger CL than max from polar computation
    inputs = {'profile:reynolds': 18000000,
              'profile:mach': 0.20,
              'profile:alpha': 20.28,
              }
    outputs = {}
    xfoil.compute(inputs, outputs)
    assert outputs['xfoil:CL'] == pytest.approx(1.9844, 1e-4)


@pytest.mark.skip('Need to be refined, as XFOIL results can be unreliable when not using polar')
def test_cl_max_from_openmdao():
    """ Tests how to get CL max using OpenMDAO """
    xfoil = XfoilPoint()
    xfoil.options['xfoil_exe_path'] = XFOIL_EXE
    xfoil.options['profile_path'] = INPUT_PROFILE

    prob = Problem()
    model = prob.model

    # create and connect inputs
    model.add_subsystem('Re', IndepVarComp('profile:reynolds', 18e6), promotes=['*'])
    model.add_subsystem('M', IndepVarComp('profile:mach', 0.20), promotes=['*'])
    model.add_subsystem('alpha', IndepVarComp('profile:alpha', 0.), promotes=['*'])
    model.add_subsystem('p', xfoil, promotes=['*'])
    model.add_subsystem('minus_CL', ExecComp('minusCL = - CL'))
    model.connect('xfoil:CL', 'minus_CL.CL')

    # find optimal solution with SciPy optimize
    # solution (minimum): x = 6.6667; y = -7.3333
    prob.driver = ScipyOptimizeDriver()
    prob.driver.options['optimizer'] = 'SLSQP'

    prob.model.add_design_var('profile:alpha', lower=0, upper=30)

    prob.model.add_objective('minus_CL.minusCL')

    prob.driver.options['tol'] = 1e-3
    prob.driver.options['disp'] = True

    prob.setup()
    prob.run_driver()

    print(prob['xfoil:alpha'])
    print(prob['xfoil:CL'])
    assert prob['minus_CL.minusCL'] == pytest.approx(-1.9408, 1e-2)
