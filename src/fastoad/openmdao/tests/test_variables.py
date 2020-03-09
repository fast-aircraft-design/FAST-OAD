"""
Module for testing VariableList.py
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

import numpy as np
import pytest

from fastoad.openmdao.variables import VariableList, Variable


def test_variables():
    """ Tests features of Variable and VariableList class"""

    # Test description overloading
    x = Variable('test:test_variable', value=500)
    assert x.description == 'for testing (do not remove)'

    # Initialization
    variables = VariableList()
    a_var = Variable('a', value=0.)
    b_var = Variable('b', value=1.)
    n_var = Variable('n', value=np.array(np.nan))
    variables['a'] = {'value': 0.}  # Tests VariableList.__setitem__ with dict input
    variables.append(b_var)  # Tests VariableList.append()
    with pytest.raises(TypeError):
        variables['z'] = 5.  # error when value is not a dict
    with pytest.raises(TypeError):
        variables[1] = 5.  # error when value is not a Variable
    with pytest.raises(TypeError):
        variables.append(5.)  # error when value is not a Variable

    variables.append(n_var)
    variables[2] = n_var  # same as line above
    del variables['n']

    # Initialization from list
    variables2 = VariableList([a_var, b_var])
    assert variables == variables2

    # tests on Variable
    assert a_var.value == 0.
    assert a_var.units is None
    assert a_var.description == ''

    assert n_var == Variable('n', value=np.array(np.nan))  # tests __eq__ with nan value

    #   __getitem___
    assert variables['a'] == a_var
    assert variables['b'] is b_var

    #   .names()
    assert list(variables.names()) == ['a', 'b']

    # Tests adding variable with existing name
    assert len(variables) == 2
    assert variables['a'].value == 0.
    variables.append(Variable('a', value=5.))
    assert len(variables) == 2
    assert variables['a'].value == 5.
    variables['a'] = {'value': 42.}
    assert variables['a'].value == 42.

    # .update()
    assert len(variables) == 2
    assert list(variables.names()) == ['a', 'b']
    variables.update([n_var])  # does nothing
    assert len(variables) == 2
    assert list(variables.names()) == ['a', 'b']

    variables.update([n_var], add_variables=True)
    assert len(variables) == 3
    assert list(variables.names()) == ['a', 'b', 'n']
    assert variables['a'].value == 42.

    variables.update([Variable('a', value=-10.), Variable('not_added', value=0.)])
    assert len(variables) == 3
    assert list(variables.names()) == ['a', 'b', 'n']
    assert variables['a'].value == -10.
