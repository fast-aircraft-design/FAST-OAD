"""
Test module for OpenMDAO checks
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

import logging
from typing import List

import numpy as np
import pytest
from numpy.testing import assert_allclose
from openmdao.core.group import Group
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.problem import Problem
from openmdao.solvers.nonlinear.nonlinear_block_gs import NonlinearBlockGS

from fastoad.exceptions import NoSetupError
from fastoad.openmdao.connections_utils import get_unconnected_inputs, \
    build_ivc_of_unconnected_inputs, build_ivc_of_variables, update_ivc
from fastoad.openmdao.variables import Variable
from tests.sellar_example.disc1 import Disc1
from tests.sellar_example.disc2 import Disc2
from tests.sellar_example.functions import Functions
from tests.sellar_example.sellar import Sellar

# Logger for this module
_LOGGER = logging.getLogger(__name__)


def test_get_unconnected_inputs():
    """ Tests get_unconnected_inputs() on a minimal problem  """
    # Check with Component as problem model -----------------------------------

    test_labels = []
    components = {}
    expected_mandatory_variables = {}
    expected_optional_variables = {}

    # Test with a problem with a single component
    test_label = 'single_component'
    test_labels.append(test_label)
    components[test_label] = Disc1()
    expected_mandatory_variables[test_label] = ['x']
    expected_optional_variables[test_label] = ['y2', 'z']

    # Test with a group problem with a single component (no promoted variable)
    test_label = 'single_component_group'
    test_labels.append(test_label)
    group = Group()
    group.add_subsystem('disc1', Disc1())
    components[test_label] = group
    expected_mandatory_variables[test_label] = ['disc1.x']
    expected_optional_variables[test_label] = ['disc1.y2', 'disc1.z']

    # Test with a group problem with one component and some input
    test_label = 'component+some_input'
    test_labels.append(test_label)
    group = Group()
    group.add_subsystem('disc1', Disc1())
    ivc = IndepVarComp()
    ivc.add_output('y2', 1.)
    group.add_subsystem('inputs', ivc)
    group.connect('inputs.y2', 'disc1.y2')
    components[test_label] = group
    expected_mandatory_variables[test_label] = ['disc1.x']
    expected_optional_variables[test_label] = ['disc1.z']

    # Test with a group problem with Sellar components
    test_label = 'Sellar_components'
    test_labels.append(test_label)
    group = Group()
    group.add_subsystem('disc1', Disc1(), promotes=['*'])
    group.add_subsystem('disc2', Disc2(), promotes=['*'])
    group.add_subsystem('functions', Functions(), promotes=['*'])
    components[test_label] = group
    expected_mandatory_variables[test_label] = ['disc1.x', 'functions.z']
    expected_optional_variables[test_label] = ['disc1.z', 'disc2.z', 'functions.x']

    # Test with the fully set Sellar problem
    test_label = 'Sellar'
    test_labels.append(test_label)
    components[test_label] = Sellar()
    expected_mandatory_variables[test_label] = []
    expected_optional_variables[test_label] = []

    for label in test_labels:
        _LOGGER.info('Testing %s -------------------' % label)
        problem = Problem(components[label])
        _test_problem(problem, expected_mandatory_variables[label],
                      expected_optional_variables[label])


def _test_problem(problem, expected_missing_mandatory_variables,
                  expected_missing_optional_variables):
    """ Tests get_unconnected_inputs for provided problem """
    # Check without setup  -> error
    with pytest.raises(NoSetupError) as exc_info:
        _, _ = get_unconnected_inputs(problem, logger=_LOGGER)
    assert exc_info is not None

    # Check after setup
    problem.setup()

    # with logger provided
    mandatory, optional = get_unconnected_inputs(problem, logger=_LOGGER)
    assert sorted(mandatory) == sorted(expected_missing_mandatory_variables)
    assert sorted(optional) == sorted(expected_missing_optional_variables)

    # without providing logger
    mandatory, optional = get_unconnected_inputs(problem)
    assert sorted(mandatory) == sorted(expected_missing_mandatory_variables)
    assert sorted(optional) == sorted(expected_missing_optional_variables)


def test_build_ivc_of_unconnected_inputs():
    def _test_and_check(problem: Problem,
                        expected_mandatory_vars: List[Variable],
                        expected_optional_vars: List[Variable]):
        problem.setup()
        ivc = build_ivc_of_unconnected_inputs(problem, with_optional_inputs=False)
        ivc_vars = [Variable(name=name, value=value, **attributes)
                    for (name, value, attributes) in ivc._indep_external]
        assert set([str(i) for i in ivc_vars]) == set(
            [str(i) for i in expected_mandatory_vars])

        ivc = build_ivc_of_unconnected_inputs(problem, with_optional_inputs=True)
        ivc_vars = [Variable(name=name, value=value, **attributes)
                    for (name, value, attributes) in ivc._indep_external]
        assert set([str(i) for i in ivc_vars]) == set(
            [str(i) for i in expected_mandatory_vars + expected_optional_vars])

    # Check with an ExplicitComponent
    problem = Problem(Disc1())
    expected_mandatory_vars = [Variable(name='x', value=np.array([np.nan]), units=None)]
    expected_optional_vars = [Variable(name='z', value=np.array([5., 2.]), units='m**2'),
                              Variable(name='y2', value=np.array([1.]), units=None)]
    _test_and_check(problem, expected_mandatory_vars, expected_optional_vars)

    # Check with a Group
    group = Group()
    group.add_subsystem('disc1', Disc1(), promotes=['*'])
    group.add_subsystem('disc2', Disc2(), promotes=['*'])
    problem = Problem(group)

    expected_mandatory_vars = [Variable(name='x', value=np.array([np.nan]), units=None)]
    expected_optional_vars = [Variable(name='z', value=np.array([5., 2.]), units='m**2')]
    _test_and_check(problem, expected_mandatory_vars, expected_optional_vars)

    # Check with the whole Sellar problem.
    # 'z' variable should now be mandatory, because it is so in Functions
    group = Group()
    group.add_subsystem('disc1', Disc1(), promotes=['*'])
    group.add_subsystem('disc2', Disc2(), promotes=['*'])
    group.add_subsystem('functions', Functions(), promotes=['*'])
    problem = Problem(group)

    expected_mandatory_vars = [Variable(name='x', value=np.array([np.nan]), units=None),
                               Variable(name='z', value=np.array([np.nan, np.nan]), units='m**2')]
    expected_optional_vars = []
    _test_and_check(problem, expected_mandatory_vars, expected_optional_vars)


def test_build_ivc_of_variables():
    def _test_and_check(problem: Problem,
                        initial_values: bool,
                        use_inputs: bool,
                        use_outputs: bool,
                        expected_vars: List[Variable]):
        ivc = build_ivc_of_variables(problem, initial_values,
                                     use_inputs=use_inputs, use_outputs=use_outputs)
        ivc_vars = [Variable(name=name, value=value, **attributes)
                    for (name, value, attributes) in ivc._indep_external]
        assert set([str(i) for i in ivc_vars]) == set(
            [str(i) for i in expected_vars])

    # Check with an ExplicitComponent
    problem = Problem(Disc1())
    expected_input_vars = [Variable(name='x', value=np.array([np.nan]), units=None),
                           Variable(name='y2', value=np.array([1.]), units=None),
                           Variable(name='z', value=np.array([5., 2.]), units='m**2')]
    expected_output_vars = [Variable(name='y1', value=np.array([1.]), units=None)]
    _test_and_check(problem, False, True, False, expected_input_vars)
    _test_and_check(problem, False, False, True, expected_output_vars)
    _test_and_check(problem, False, True, True, expected_input_vars + expected_output_vars)

    # Check with a Group
    group = Group()
    group.add_subsystem('disc1', Disc1(), promotes=['*'])
    group.add_subsystem('disc2', Disc2(), promotes=['*'])
    problem = Problem(group)

    # All variables are inputs somewhere
    expected_input_vars = [Variable(name='x', value=np.array([np.nan]), units=None),
                           Variable(name='y1', value=np.array([1.]), units=None),
                           Variable(name='y2', value=np.array([1.]), units=None),
                           Variable(name='z', value=np.array([5., 2.]), units='m**2')]
    expected_output_vars = [Variable(name='y1', value=np.array([1.]), units=None),
                            Variable(name='y2', value=np.array([1.]), units=None)]
    _test_and_check(problem, False, True, False, expected_input_vars)
    _test_and_check(problem, False, False, True, expected_output_vars)
    _test_and_check(problem, False, True, True, expected_input_vars)

    # Check with the whole Sellar problem, without computation.
    group = Group()
    indeps = group.add_subsystem('indeps', IndepVarComp(), promotes=['*'])
    indeps.add_output('x', 1., units='Pa')  # This setting of units will prevail in our output
    indeps.add_output('z', [5., 2.], units='m**2')
    group.add_subsystem('disc1', Disc1(), promotes=['*'])
    group.add_subsystem('disc2', Disc2(), promotes=['*'])
    group.add_subsystem('functions', Functions(), promotes=['*'])
    group.nonlinear_solver = NonlinearBlockGS()
    problem = Problem(group)

    expected_input_vars = [Variable(name='x', value=np.array([np.nan]), units=None),
                           Variable(name='z', value=np.array([5., 2.]), units='m**2'),
                           Variable(name='y1', value=np.array([1.]), units=None),
                           Variable(name='y2', value=np.array([1.]), units=None)]
    expected_output_vars = [Variable(name='x', value=np.array([1.]), units='Pa'),
                            Variable(name='z', value=np.array([5., 2.]), units='m**2'),
                            Variable(name='y1', value=np.array([1.]), units=None),
                            Variable(name='y2', value=np.array([1.]), units=None),
                            Variable(name='g1', value=np.array([1.]), units=None),
                            Variable(name='g2', value=np.array([1.]), units=None),
                            Variable(name='f', value=np.array([1.]), units=None)]
    _test_and_check(problem, True, True, False, expected_input_vars)
    _test_and_check(problem, True, False, True, expected_output_vars)

    # Check with the whole Sellar problem, with computation.
    expected_computed_output_vars = [Variable(name='x', value=np.array([1.]), units='Pa'),
                                     Variable(name='z', value=np.array([5., 2.]), units='m**2'),
                                     Variable(name='y1', value=np.array([25.58830237]), units=None),
                                     Variable(name='y2', value=np.array([12.05848815]), units=None),
                                     Variable(name='g1', value=np.array([-22.42830237]),
                                              units=None),
                                     Variable(name='g2', value=np.array([-11.94151185]),
                                              units=None),
                                     Variable(name='f', value=np.array([28.58830817]), units=None)]
    problem.setup()
    problem.run_model()
    _test_and_check(problem, True, True, False, expected_input_vars)
    _test_and_check(problem, True, False, True, expected_output_vars)
    _test_and_check(problem, False, False, True, expected_computed_output_vars)

    # Check with the whole Sellar problem without promotions, without computation.
    group = Group()
    indeps = group.add_subsystem('indeps', IndepVarComp())
    indeps.add_output('x', 1., units='Pa')
    indeps.add_output('z', [5., 2.], units='m**2')
    group.add_subsystem('disc2', Disc2())
    group.add_subsystem('disc1', Disc1())
    group.add_subsystem('functions', Functions())
    group.nonlinear_solver = NonlinearBlockGS()
    group.connect('indeps.x', 'disc1.x')
    group.connect('indeps.x', 'functions.x')
    group.connect('indeps.z', 'disc1.z')
    group.connect('indeps.z', 'disc2.z')
    group.connect('indeps.z', 'functions.z')
    group.connect('disc1.y1', 'disc2.y1')
    group.connect('disc1.y1', 'functions.y1')
    group.connect('disc2.y2', 'disc1.y2')
    group.connect('disc2.y2', 'functions.y2')

    problem = Problem(group)

    expected_vars = [
        Variable(name='indeps.x', value=np.array([1.]), units='Pa'),
        Variable(name='indeps.z', value=np.array([5., 2.]), units='m**2'),
        Variable(name='disc1.x', value=np.array([np.nan]), units=None),
        Variable(name='disc1.z', value=np.array([5., 2.]), units='m**2'),
        Variable(name='disc1.y1', value=np.array([1.]), units=None),
        Variable(name='disc1.y2', value=np.array([1.]), units=None),
        Variable(name='disc2.z', value=np.array([5., 2.]), units='m**2'),
        Variable(name='disc2.y1', value=np.array([1.]), units=None),
        Variable(name='disc2.y2', value=np.array([1.]), units=None),
        Variable(name='functions.x', value=np.array([2]), units=None),
        Variable(name='functions.z', value=np.array([np.nan, np.nan]), units='m**2'),
        Variable(name='functions.y1', value=np.array([1.]), units=None),
        Variable(name='functions.y2', value=np.array([1.]), units=None),
        Variable(name='functions.g1', value=np.array([1.]), units=None),
        Variable(name='functions.g2', value=np.array([1.]), units=None),
        Variable(name='functions.f', value=np.array([1.]), units=None)
    ]
    _test_and_check(problem, True, True, True, expected_vars)
    expected_computed_vars = [  # Here links are done, even without computations
        Variable(name='indeps.x', value=np.array([1.]), units='Pa'),
        Variable(name='indeps.z', value=np.array([5., 2.]), units='m**2'),
        Variable(name='disc1.x', value=np.array([1.]), units=None),
        Variable(name='disc1.z', value=np.array([5., 2.]), units='m**2'),
        Variable(name='disc1.y1', value=np.array([1.]), units=None),
        Variable(name='disc1.y2', value=np.array([1.]), units=None),
        Variable(name='disc2.z', value=np.array([5., 2.]), units='m**2'),
        Variable(name='disc2.y1', value=np.array([1.]), units=None),
        Variable(name='disc2.y2', value=np.array([1.]), units=None),
        Variable(name='functions.x', value=np.array([1.]), units=None),
        Variable(name='functions.z', value=np.array([5., 2.]), units='m**2'),
        Variable(name='functions.y1', value=np.array([1.]), units=None),
        Variable(name='functions.y2', value=np.array([1.]), units=None),
        Variable(name='functions.g1', value=np.array([1.]), units=None),
        Variable(name='functions.g2', value=np.array([1.]), units=None),
        Variable(name='functions.f', value=np.array([1.]), units=None)
    ]
    _test_and_check(problem, False, True, True, expected_computed_vars)

    # Check with the whole Sellar problem without promotions, with computation.
    expected_computed_vars = [
        Variable(name='indeps.x', value=np.array([1.]), units='Pa'),
        Variable(name='indeps.z', value=np.array([5., 2.]), units='m**2'),
        Variable(name='disc1.x', value=np.array([1.]), units=None),
        Variable(name='disc1.z', value=np.array([5., 2.]), units='m**2'),
        Variable(name='disc1.y1', value=np.array([25.58830237]), units=None),
        Variable(name='disc1.y2', value=np.array([12.05848815]), units=None),
        Variable(name='disc2.z', value=np.array([5., 2.]), units='m**2'),
        Variable(name='disc2.y1', value=np.array([25.58830237]), units=None),
        Variable(name='disc2.y2', value=np.array([12.05848815]), units=None),
        Variable(name='functions.x', value=np.array([1.]), units=None),
        Variable(name='functions.z', value=np.array([5., 2.]), units='m**2'),
        Variable(name='functions.y1', value=np.array([25.58830237]), units=None),
        Variable(name='functions.y2', value=np.array([12.05848815]), units=None),
        Variable(name='functions.g1', value=np.array([-22.42830237]), units=None),
        Variable(name='functions.g2', value=np.array([-11.94151185]), units=None),
        Variable(name='functions.f', value=np.array([28.58830817]), units=None)
    ]
    problem.setup()
    problem.run_model()
    _test_and_check(problem, True, True, True, expected_vars)
    _test_and_check(problem, False, True, True, expected_computed_vars)


def test_update_ivc():
    def create_sellar_problem():
        # Build a Sellar problem
        group = Group()
        group.add_subsystem('disc1', Disc1(), promotes=['*'])
        group.add_subsystem('disc2', Disc2(), promotes=['*'])
        group.add_subsystem('functions', Functions(), promotes=['*'])
        return Problem(group)

    # Test without IndepVarComp (just to see)
    sellar = create_sellar_problem()
    sellar.setup()
    sellar.run_model()
    assert np.isnan(sellar['f'])

    # Test with an IndepVarcomp
    ivc = IndepVarComp()
    ivc.add_output('x', 0.)
    ivc.add_output('z', [0., 0.])

    sellar.model.add_subsystem('inputs', ivc, promotes=['*'])
    sellar.setup()
    sellar.run_model()
    assert_allclose(0.439407, sellar['f'], rtol=1e-5)

    # Test with the updated IndepVarcomp
    ivc_ref = IndepVarComp()
    ivc_ref.add_output('y1', 1.)  # If this one is kept in updated_ivc, run_model() will fail
    ivc_ref.add_output('z', [5., 2.])

    updated_ivc = update_ivc(ivc, ivc_ref)

    sellar = create_sellar_problem()
    sellar.model.add_subsystem('inputs', updated_ivc, promotes=['*'])
    sellar.setup()
    sellar.run_model()
    assert_allclose(28.800005, sellar['f'], rtol=1e-5)
