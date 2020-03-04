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
import openmdao.api as om
import pytest

from fastoad.exceptions import NoSetupError
from .sellar_example.disc1 import Disc1
from .sellar_example.disc2 import Disc2
from .sellar_example.functions import Functions
from .sellar_example.sellar import Sellar
from ..connections_utils import get_unconnected_input_names, get_ivc_from_variables, \
    get_variables_from_ivc, get_unconnected_input_variables, get_variables_from_problem, \
    get_df_from_variables, get_variables_from_df
from ..variables import Variable, VariableList

# Logger for this module
_LOGGER = logging.getLogger(__name__)


def test_ivc_from_to_variables():
    vars = VariableList()
    vars['a'] = {'value': 5}
    vars['b'] = {'value': 2.5, 'units': 'm'}
    vars['c'] = {'value': -3.2, 'units': 'kg/s', 'desc': 'some test'}

    ivc = get_ivc_from_variables(vars)
    new_vars = get_variables_from_ivc(ivc)

    assert vars.names() == new_vars.names()
    for var, new_var in zip(vars, new_vars):
        assert var == new_var


def test_df_from_to_variables():
    vars = VariableList()
    vars['a'] = {'value': 5}
    vars['b'] = {'value': 2.5, 'units': 'm'}
    vars['c'] = {'value': -3.2, 'units': 'kg/s', 'desc': 'some test'}

    df = get_df_from_variables(vars)
    new_vars = get_variables_from_df(df)

    assert vars.names() == new_vars.names()
    for var, new_var in zip(vars, new_vars):
        assert var == new_var


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
    group = om.Group()
    group.add_subsystem('disc1', Disc1())
    components[test_label] = group
    expected_mandatory_variables[test_label] = ['disc1.x']
    expected_optional_variables[test_label] = ['disc1.y2', 'disc1.z']

    # Test with a group problem with one component and some input
    test_label = 'component+some_input'
    test_labels.append(test_label)
    group = om.Group()
    group.add_subsystem('disc1', Disc1())
    ivc = om.IndepVarComp()
    ivc.add_output('y2', 1.)
    group.add_subsystem('inputs', ivc)
    group.connect('inputs.y2', 'disc1.y2')
    components[test_label] = group
    expected_mandatory_variables[test_label] = ['disc1.x']
    expected_optional_variables[test_label] = ['disc1.z']

    # Test with a group problem with Sellar components
    test_label = 'Sellar_components'
    test_labels.append(test_label)
    group = om.Group()
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
        problem = om.Problem(components[label])
        _test_problem(problem, expected_mandatory_variables[label],
                      expected_optional_variables[label])


def _test_problem(problem, expected_missing_mandatory_variables,
                  expected_missing_optional_variables):
    """ Tests get_unconnected_inputs for provided problem """
    # Check without setup  -> error
    with pytest.raises(NoSetupError) as exc_info:
        _, _ = get_unconnected_input_names(problem, logger=_LOGGER)
    assert exc_info is not None

    # Check after setup
    problem.setup()

    # with logger provided
    mandatory, optional = get_unconnected_input_names(problem, logger=_LOGGER)
    assert sorted(mandatory) == sorted(expected_missing_mandatory_variables)
    assert sorted(optional) == sorted(expected_missing_optional_variables)

    # without providing logger
    mandatory, optional = get_unconnected_input_names(problem)
    assert sorted(mandatory) == sorted(expected_missing_mandatory_variables)
    assert sorted(optional) == sorted(expected_missing_optional_variables)


def test_get_unconnected_input_variables():
    def _test_and_check(problem: om.Problem,
                        expected_mandatory_vars: List[Variable],
                        expected_optional_vars: List[Variable]):
        problem.setup()
        vars = get_unconnected_input_variables(problem, with_optional_inputs=False)
        assert vars == expected_mandatory_vars

        vars = get_unconnected_input_variables(problem, with_optional_inputs=True)
        assert vars == expected_mandatory_vars + expected_optional_vars

    # Check with an ExplicitComponent
    problem = om.Problem(Disc1())
    expected_mandatory_vars = [Variable(name='x', value=np.array([np.nan]), units=None)]
    expected_optional_vars = [Variable(name='z', value=np.array([5., 2.]), units='m**2'),
                              Variable(name='y2', value=np.array([1.]), units=None)]
    _test_and_check(problem, expected_mandatory_vars, expected_optional_vars)

    # Check with a Group
    group = om.Group()
    group.add_subsystem('disc1', Disc1(), promotes=['*'])
    group.add_subsystem('disc2', Disc2(), promotes=['*'])
    problem = om.Problem(group)

    expected_mandatory_vars = [Variable(name='x', value=np.array([np.nan]), units=None)]
    expected_optional_vars = [Variable(name='z', value=np.array([5., 2.]), units='m**2')]
    _test_and_check(problem, expected_mandatory_vars, expected_optional_vars)

    # Check with the whole Sellar problem.
    # 'z' variable should now be mandatory, because it is so in Functions
    group = om.Group()
    group.add_subsystem('disc1', Disc1(), promotes=['*'])
    group.add_subsystem('disc2', Disc2(), promotes=['*'])
    group.add_subsystem('functions', Functions(), promotes=['*'])
    problem = om.Problem(group)

    expected_mandatory_vars = [Variable(name='x', value=np.array([np.nan]), units=None),
                               Variable(name='z', value=np.array([np.nan, np.nan]), units='m**2')]
    expected_optional_vars = []
    _test_and_check(problem, expected_mandatory_vars, expected_optional_vars)


def test_get_variables_from_problem():
    def _test_and_check(problem: om.Problem,
                        initial_values: bool,
                        use_inputs: bool,
                        use_outputs: bool,
                        expected_vars: List[Variable]):
        vars = get_variables_from_problem(problem, initial_values,
                                          use_inputs=use_inputs, use_outputs=use_outputs)

        # A comparison of sets will not work due to values not being stricly equal
        # (not enough decimals in expected values), so we do not use this:
        # assert set(vars) == set(expected_vars)

        # So we do comparison as strings, after having removed tags from metadata, that
        # depend on variable source
        for var in vars + expected_vars:
            var.metadata['tags'] = set()

        assert set([str(i) for i in vars]) == set([str(i) for i in expected_vars])

    # Check with an ExplicitComponent
    problem = om.Problem(Disc1())
    expected_input_vars = [Variable(name='x', value=np.array([np.nan]), units=None),
                           Variable(name='y2', value=np.array([1.]), units=None),
                           Variable(name='z', value=np.array([5., 2.]), units='m**2')]
    expected_output_vars = [Variable(name='y1', value=np.array([1.]), units=None)]
    _test_and_check(problem, False, True, False, expected_input_vars)
    _test_and_check(problem, False, False, True, expected_output_vars)
    _test_and_check(problem, False, True, True, expected_input_vars + expected_output_vars)

    # Check with a Group
    group = om.Group()
    group.add_subsystem('disc1', Disc1(), promotes=['*'])
    group.add_subsystem('disc2', Disc2(), promotes=['*'])
    problem = om.Problem(group)

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
    group = om.Group()
    indeps = group.add_subsystem('indeps', om.IndepVarComp(), promotes=['*'])
    indeps.add_output('x', 1., units='Pa')  # This setting of units will prevail in our output
    indeps.add_output('z', [5., 2.], units='m**2')
    group.add_subsystem('disc1', Disc1(), promotes=['*'])
    group.add_subsystem('disc2', Disc2(), promotes=['*'])
    group.add_subsystem('functions', Functions(), promotes=['*'])
    group.nonlinear_solver = om.NonlinearBlockGS(reraise_child_analysiserror=False)
    problem = om.Problem(group)

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
                                     Variable(name='f', value=np.array([28.58830817]), units=None),
                                     Variable(name='g1', value=np.array([-22.42830237]),
                                              units=None),
                                     Variable(name='g2', value=np.array([-11.94151185]),
                                              units=None)]
    problem.setup()
    problem.run_model()
    _test_and_check(problem, True, True, False, expected_input_vars)
    _test_and_check(problem, True, False, True, expected_output_vars)
    _test_and_check(problem, False, False, True, expected_computed_output_vars)

    # Check with the whole Sellar problem without promotions, without computation.
    group = om.Group()
    indeps = group.add_subsystem('indeps', om.IndepVarComp())
    indeps.add_output('x', 1., units='Pa')
    indeps.add_output('z', [5., 2.], units='m**2')
    group.add_subsystem('disc2', Disc2())
    group.add_subsystem('disc1', Disc1())
    group.add_subsystem('functions', Functions())
    group.nonlinear_solver = om.NonlinearBlockGS(reraise_child_analysiserror=False)
    group.connect('indeps.x', 'disc1.x')
    group.connect('indeps.x', 'functions.x')
    group.connect('indeps.z', 'disc1.z')
    group.connect('indeps.z', 'disc2.z')
    group.connect('indeps.z', 'functions.z')
    group.connect('disc1.y1', 'disc2.y1')
    group.connect('disc1.y1', 'functions.y1')
    group.connect('disc2.y2', 'disc1.y2')
    group.connect('disc2.y2', 'functions.y2')

    problem = om.Problem(group)

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
