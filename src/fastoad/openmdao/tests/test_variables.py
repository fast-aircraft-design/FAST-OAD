"""
Module for testing VariableList.py
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
import openmdao.api as om
import pytest

from ..variables import VariableList, Variable


def test_variables():
    """ Tests features of Variable and VariableList class"""

    # Test description overloading
    x = Variable("test:test_variable", value=500)
    assert x.description == "for testing (do not remove, keep first)"

    # Initialization
    variables = VariableList()
    a_var = Variable("a", value=0.0)
    b_var = Variable("b", value=1.0)
    n_var = Variable("n", value=np.array(np.nan))
    variables["a"] = {"value": 0.0}  # Tests VariableList.__setitem__ with dict input
    variables.append(b_var)  # Tests VariableList.append()
    with pytest.raises(TypeError):
        variables["z"] = 5.0  # error when value is not a dict
    with pytest.raises(TypeError):
        variables[1] = 5.0  # error when value is not a Variable
    with pytest.raises(TypeError):
        variables.append(5.0)  # error when value is not a Variable

    variables.append(n_var)
    variables[2] = n_var  # same as line above
    del variables["n"]

    # Initialization from list
    variables2 = VariableList([a_var, b_var])
    assert variables == variables2

    # tests on Variable
    assert a_var.value == 0.0
    assert a_var.units is None
    assert a_var.description == ""

    assert n_var == Variable("n", value=np.array(np.nan))  # tests __eq__ with nan value

    #   __getitem___
    assert variables["a"] == a_var
    assert variables["b"] is b_var

    #   .names()
    assert list(variables.names()) == ["a", "b"]

    # Tests adding variable with existing name
    assert len(variables) == 2
    assert variables["a"].value == 0.0
    variables.append(Variable("a", value=5.0))
    assert len(variables) == 2
    assert variables["a"].value == 5.0
    variables["a"] = {"value": 42.0}
    assert variables["a"].value == 42.0

    # .update()
    assert len(variables) == 2
    assert list(variables.names()) == ["a", "b"]
    variables.update([n_var])  # does nothing
    assert len(variables) == 2
    assert list(variables.names()) == ["a", "b"]

    variables.update([n_var], add_variables=True)
    assert len(variables) == 3
    assert list(variables.names()) == ["a", "b", "n"]
    assert variables["a"].value == 42.0

    variables.update([Variable("a", value=-10.0), Variable("not_added", value=0.0)])
    assert len(variables) == 3
    assert list(variables.names()) == ["a", "b", "n"]
    assert variables["a"].value == -10.0


def test_ivc_from_to_variables():
    """
    Tests VariableList.to_ivc() and VariableList.from_ivc()
    """
    vars = VariableList()
    vars["a"] = {"value": 5}
    vars["b"] = {"value": 2.5, "units": "m"}
    vars["c"] = {"value": -3.2, "units": "kg/s", "desc": "some test"}

    ivc = vars.to_ivc()
    problem = om.Problem(ivc)
    problem.setup()
    assert problem["a"] == 5
    assert problem.get_val("b", units="cm") == 250
    assert problem.get_val("c", units="kg/ms") == -0.0032

    new_vars = VariableList.from_ivc(ivc)
    assert vars.names() == new_vars.names()
    for var, new_var in zip(vars, new_vars):
        assert var == new_var


def test_df_from_to_variables():
    """
    Tests VariableList.to_dataframe() and VariableList.from_dataframe()
    """
    vars = VariableList()
    vars["a"] = {"value": 5}
    vars["b"] = {"value": np.array([1.0, 2.0, 3.0]), "units": "m"}
    vars["c"] = {"value": [1.0, 2.0, 3.0], "units": "kg/s", "desc": "some test"}

    df = vars.to_dataframe()
    assert np.all(df["Name"] == ["a", "b", "c"])
    assert np.all(df["Value"] == [5, [1.0, 2.0, 3.0], [1.0, 2.0, 3.0]])
    assert np.all(df["Unit"].to_list() == [None, "m", "kg/s"])
    assert np.all(df["Description"].to_list() == ["", "", "some test"])

    new_vars = VariableList.from_dataframe(df)

    assert vars.names() == new_vars.names()
    for var, new_var in zip(vars, new_vars):
        assert var == new_var
