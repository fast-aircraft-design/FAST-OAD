"""
Test module for OpenMDAO checks
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

import logging
from typing import List

import numpy as np
import pytest
from openmdao.core.group import Group
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.problem import Problem

from fastoad.exceptions import NoSetupError
from fastoad.openmdao.connections_utils import get_unconnected_inputs, \
    get_vars_of_unconnected_inputs, build_ivc_of_unconnected_inputs
from fastoad.openmdao.types import Variable
from tests.io.xml.data.a_airframe.airframe import Airframe
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


def test_get_variables_of_unconnected_inputs():

    def _test_and_check(problem,
                        expected_mandatory_vars: List[Variable],
                        expected_optional_vars: List[Variable]):
        problem.setup()
        mandatory_vars_prom, optional_vars_prom = get_vars_of_unconnected_inputs(problem)

        assert set([str(i) for i in mandatory_vars_prom]) == set(
            [str(i) for i in expected_mandatory_vars])
        assert set([str(i) for i in optional_vars_prom]) == set(
            [str(i) for i in expected_optional_vars])

    # Check with an ExplicitComponent
    problem = Problem(Disc1())
    expected_mandatory_vars = [Variable(name='x', value=np.array([np.nan]), units=None)]
    expected_optional_vars = [Variable(name='z', value=np.array([5., 2.]), units=None),
                              Variable(name='y2', value=np.array([1.]), units=None)]
    _test_and_check(problem, expected_mandatory_vars, expected_optional_vars)

    # Check with a Group
    group = Group()
    group.add_subsystem('disc1', Disc1(), promotes=['*'])
    group.add_subsystem('disc2', Disc2(), promotes=['*'])
    problem = Problem(group)

    expected_mandatory_vars = [Variable(name='x', value=np.array([np.nan]), units=None)]
    expected_optional_vars = [Variable(name='z', value=np.array([5., 2.]), units=None)]
    _test_and_check(problem, expected_mandatory_vars, expected_optional_vars)

    # Check with the whole Sellar problem.
    # 'z' variable should now be mandatory, because it is so in Functions
    group = Group()
    group.add_subsystem('disc1', Disc1(), promotes=['*'])
    group.add_subsystem('disc2', Disc2(), promotes=['*'])
    group.add_subsystem('functions', Functions(), promotes=['*'])
    problem = Problem(group)

    expected_mandatory_vars = [Variable(name='x', value=np.array([np.nan]), units=None),
                               Variable(name='z', value=np.array([np.nan, np.nan]), units=None)]
    expected_optional_vars = []
    _test_and_check(problem, expected_mandatory_vars, expected_optional_vars)


def test_build_ivc_of_unconnected_inputs():
    known_optional_var_prom = Variable('kfactors_a1:K_A1', np.array([1.]), None)
    known_mandatory_var_prom = Variable('geometry:wing_area', np.array([np.nan]), 'm**2')

    system = Airframe()

    problem = Problem(system)
    problem.setup()

    ivc_no_opt = build_ivc_of_unconnected_inputs(problem, optional_inputs=False)
    ivc_with_opt = build_ivc_of_unconnected_inputs(problem, optional_inputs=True)

    outputs_no_opt = []
    for (name, value, attributes) in ivc_no_opt._indep_external:  # pylint: disable=protected-access
        outputs_no_opt.append(Variable(name, value, attributes['units']))

    outputs_with_opt = []
    for (
            name, value,
            attributes) in ivc_with_opt._indep_external:  # pylint: disable=protected-access
        outputs_with_opt.append(Variable(name, value, attributes['units']))

    assert len(outputs_with_opt) == 54
    assert len(outputs_no_opt) == 23
    assert not (str(known_optional_var_prom) in [str(i) for i in outputs_no_opt])
    assert (str(known_optional_var_prom) in [str(i) for i in outputs_with_opt])
    assert (str(known_mandatory_var_prom) in [str(i) for i in outputs_no_opt])
    assert (str(known_mandatory_var_prom) in [str(i) for i in outputs_with_opt])
