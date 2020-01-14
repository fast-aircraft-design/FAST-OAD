"""
Module for testing Variables.py
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

from fastoad.openmdao.variables import Variables, Variable


def test_variables_set_get_item():
    """ Tests features of Variable and Variables class"""
    # Initialization
    variables = Variables()
    a_var = Variable('a', value=0.)
    b_var = Variable('b', value=1.)
    variables['a'] = {'value': 0.}
    variables.append(b_var)

    # tests
    assert a_var.value == 0.
    assert a_var.units is None
    assert a_var.description is None

    assert variables['a'] == a_var
    a_var.units = "m"
    assert variables['a'] != a_var

    assert variables['b'] is b_var

    assert 'a' in variables.names()
    assert 'b' in variables.names()
    assert 'c' not in variables.names()
    assert b_var in variables

    assert len(variables) == 2
    del variables['a']
    assert len(variables) == 1
    assert 'a' not in variables.names()
    assert 'b' in variables.names()
