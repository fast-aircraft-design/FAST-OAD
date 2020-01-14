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

from fastoad.openmdao.variables import VariableList, Variable


def test_variables_set_get_item():
    """ Tests features of Variable and VariableList class"""

    # Test description overloading
    x = Variable('test:test_variable', value=500)
    assert x.description == 'for testing (do not remove)'

    # Initialization
    variables = VariableList()
    a_var = Variable('a', value=0.)
    b_var = Variable('b', value=1.)
    variables['a'] = {'value': 0.}  # Tests VariableList.__setitem__ with dict input
    variables.append(b_var)  # Tests VariableList.append()

    # tests on Variable
    assert a_var.value == 0.
    assert a_var.units is None
    assert a_var.description == ''

    # tests on VariableList
    #   __getitem___
    assert variables['a'] == a_var
    a_var.units = "m"
    assert variables['a'] != a_var

    assert variables['b'] is b_var

    #   __contains__
    assert 'a' in variables.names()
    assert 'b' in variables.names()
    assert 'c' not in variables.names()
    assert b_var in variables

    #   __len__ and __delitem__
    assert len(variables) == 2
    del variables['a']
    assert len(variables) == 1
    assert 'a' not in variables.names()
    assert 'b' in variables.names()

    #   additional tests for __setitem__  with Variable input
    variables['a'] = a_var  # adds variable with its actual name
    assert a_var in variables
    del variables['a']

    variables['c'] = a_var  # adds variable with a different name
    assert a_var not in variables  # a different instance has been stored, with 'c' as name
    assert 'c' in variables.names()
    assert variables['c'].metadata == a_var.metadata
