"""
Module for testing Variables.py
"""
#        This file is part of FAST : A framework for rapid Overall Aircraft Design
#        Copyright (C) 2020  ONERA/ISAE
#
#        FAST is free software: you can redistribute it and/or modify
#        it under the terms of the GNU General Public License as published by
#        the Free Software Foundation, either version 3 of the License, or
#        (at your option) any later version.
#
#        This program is distributed in the hope that it will be useful,
#        but WITHOUT ANY WARRANTY; without even the implied warranty of
#        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#        GNU General Public License for more details.
#
#        You should have received a copy of the GNU General Public License
#        along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

from fastoad.openmdao.variables import Variables, Variable


def test_variables_set_get_item():
    variables = Variables()
    variables['a'] = {'value': 0.}
    variables.append(Variable('b', value=1.))
    assert variables['a'].value == 0.
    assert variables['b'].value == 1.

    assert 'a' in variables.names()
    assert 'b' in variables.names()
    assert 'c' not in variables.names()
