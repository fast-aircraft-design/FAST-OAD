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

from typing import List

import numpy as np
import openmdao.api as om
import pytest
from numpy.testing import assert_allclose

from .sellar_example.disc1 import Disc1
from .sellar_example.disc2 import Disc2
from .sellar_example.functions import Functions
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
    problem = om.Problem()
    problem.model.add_subsystem("ivc", ivc, promotes=["*"])
    problem.setup()
    assert problem["a"] == 5
    assert problem["b"] == 2.5
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
    assert np.all(df["name"] == ["a", "b", "c"])
    assert np.all(df["value"] == [5, [1.0, 2.0, 3.0], [1.0, 2.0, 3.0]])
    assert np.all(df["units"].to_list() == [None, "m", "kg/s"])
    assert np.all(df["desc"].to_list() == ["", "", "some test"])

    new_vars = VariableList.from_dataframe(df)

    assert vars.names() == new_vars.names()
    for var, new_var in zip(vars, new_vars):
        assert var == new_var


def test_get_variables_from_system():
    def _test_and_check(
        component, expected_vars: List[Variable],
    ):
        vars = VariableList.from_system(component)

        # A comparison of sets will not work due to values not being strictly equal
        # (not enough decimals in expected values), so we do not use this:
        # assert set(vars) == set(expected_vars)
        # Simply comparing variable name, units and approximate value will do for here.
        sort_key = lambda v: v.name
        vars.sort(key=sort_key)
        expected_vars.sort(key=sort_key)
        for var, expected_var in zip(vars, expected_vars):
            assert var.name == expected_var.name
            assert_allclose(var.value, expected_var.value)
            assert var.units == expected_var.units

    # test Component -----------------------------------------------------------
    comp = Disc1()
    expected_vars = [
        Variable(name="x", value=np.array([np.nan]), units=None),
        Variable(name="y2", value=np.array([1.0]), units=None),
        Variable(name="z", value=np.array([5.0, 2.0]), units="m**2"),
        Variable(name="y1", value=np.array([1.0]), units=None),
    ]
    _test_and_check(comp, expected_vars)

    # test Group ---------------------------------------------------------------
    group = om.Group()
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])

    expected_vars = [
        Variable(name="x", value=np.array([np.nan]), units=None),
        Variable(name="y1", value=np.array([1.0]), units=None),
        Variable(name="y2", value=np.array([1.0]), units=None),
        Variable(name="z", value=np.array([5.0, 2.0]), units="m**2"),
    ]

    _test_and_check(group, expected_vars)


def test_get_variables_from_problem():
    def _test_and_check(
        problem: om.Problem, use_initial_values: bool, expected_vars: List[Variable],
    ):
        vars = VariableList.from_problem(problem, use_initial_values)

        # A comparison of sets will not work due to values not being strictly equal
        # (not enough decimals in expected values), so we do not use this:
        # assert set(vars) == set(expected_vars)
        # Simply comparing variable name, units and approximate value will do for here.
        sort_key = lambda v: v.name
        vars.sort(key=sort_key)
        expected_vars.sort(key=sort_key)
        for var, expected_var in zip(vars, expected_vars):
            assert var.name == expected_var.name
            assert_allclose(var.value, expected_var.value)
            assert var.units == expected_var.units
            assert var.is_input == expected_var.is_input

    # Check with an ExplicitComponent ------------------------------------------
    problem = om.Problem()
    problem.model.add_subsystem("disc1", Disc1(), promotes=["*"])
    expected_vars = [
        Variable(name="x", value=np.array([np.nan]), units=None, is_input=True),
        Variable(name="y2", value=np.array([1.0]), units=None, is_input=True),
        Variable(name="z", value=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="y1", value=np.array([1.0]), units=None, is_input=False),
    ]
    _test_and_check(problem, False, expected_vars)

    # Check with a Group -------------------------------------------------------
    group = om.Group()
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])
    problem = om.Problem(group)

    expected_vars = [
        Variable(name="x", value=np.array([np.nan]), units=None, is_input=True),
        Variable(name="y1", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="y2", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="z", value=np.array([5.0, 2.0]), units="m**2", is_input=True),
    ]

    _test_and_check(problem, False, expected_vars)

    # Check with the whole Sellar problem --------------------------------------
    # WITH promotions, WITHOUT computation
    group = om.Group()
    indeps = group.add_subsystem("indeps", om.IndepVarComp(), promotes=["*"])
    indeps.add_output("x", 1.0, units="Pa")  # This setting of units will prevail in our output
    indeps.add_output("z", [5.0, 2.0], units="m**2")
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])
    group.add_subsystem("functions", Functions(), promotes=["*"])
    group.nonlinear_solver = om.NonlinearBlockGS()
    problem = om.Problem(group)

    expected_vars = [
        Variable(name="x", value=np.array([1.0]), units="Pa", is_input=True),
        Variable(name="z", value=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="y1", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="y2", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="g1", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="g2", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="f", value=np.array([1.0]), units=None, is_input=False),
    ]
    _test_and_check(problem, True, expected_vars)

    # Check with the whole Sellar problem --------------------------------------
    # WITH promotions, WITH computation
    expected_vars = [
        Variable(name="x", value=np.array([1.0]), units="Pa", is_input=True),
        Variable(name="z", value=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="y1", value=np.array([25.58830237]), units=None, is_input=False),
        Variable(name="y2", value=np.array([12.05848815]), units=None, is_input=False),
        Variable(name="f", value=np.array([28.58830817]), units=None, is_input=False),
        Variable(name="g1", value=np.array([-22.42830237]), units=None, is_input=False),
        Variable(name="g2", value=np.array([-11.94151185]), units=None, is_input=False),
    ]
    problem.setup()
    problem.run_model()
    _test_and_check(problem, False, expected_vars)

    # Check with the whole Sellar problem --------------------------------------
    # WITHOUT promotions, WITHOUT computation
    group = om.Group()
    indeps = group.add_subsystem("indeps", om.IndepVarComp())
    indeps.add_output("x", 1.0, units="Pa")
    indeps.add_output("z", [5.0, 2.0], units="m**2")
    group.add_subsystem("disc2", Disc2())
    group.add_subsystem("disc1", Disc1())
    group.add_subsystem("functions", Functions())
    group.nonlinear_solver = om.NonlinearBlockGS()
    group.connect("indeps.x", "disc1.x")
    group.connect("indeps.x", "functions.x")
    group.connect("indeps.z", "disc1.z")
    group.connect("indeps.z", "disc2.z")
    group.connect("indeps.z", "functions.z")
    group.connect("disc1.y1", "disc2.y1")
    group.connect("disc1.y1", "functions.y1")
    group.connect("disc2.y2", "disc1.y2")
    group.connect("disc2.y2", "functions.y2")

    problem = om.Problem(group)

    expected_vars = [
        Variable(name="indeps.x", value=np.array([1.0]), units="Pa", is_input=True),
        Variable(name="indeps.z", value=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="disc1.x", value=np.array([np.nan]), units=None, is_input=True),
        Variable(name="disc1.z", value=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="disc1.y1", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="disc1.y2", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="disc2.z", value=np.array([5.0, 2.0]), units="m**2", is_input=False),
        Variable(name="disc2.y1", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="disc2.y2", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="functions.x", value=np.array([2]), units=None, is_input=True),
        Variable(name="functions.z", value=np.array([np.nan, np.nan]), units="m**2", is_input=True),
        Variable(name="functions.y1", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="functions.y2", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="functions.g1", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="functions.g2", value=np.array([1.0]), units=None, is_input=False),
        Variable(name="functions.f", value=np.array([1.0]), units=None, is_input=False),
    ]
    _test_and_check(problem, True, expected_vars)
    expected_computed_vars = [  # Here links are done, even without computations
        Variable(name="indeps.x", value=np.array([1.0]), units="Pa"),
        Variable(name="indeps.z", value=np.array([5.0, 2.0]), units="m**2"),
        Variable(name="disc1.x", value=np.array([1.0]), units=None),
        Variable(name="disc1.z", value=np.array([5.0, 2.0]), units="m**2"),
        Variable(name="disc1.y1", value=np.array([1.0]), units=None),
        Variable(name="disc1.y2", value=np.array([1.0]), units=None),
        Variable(name="disc2.z", value=np.array([5.0, 2.0]), units="m**2"),
        Variable(name="disc2.y1", value=np.array([1.0]), units=None),
        Variable(name="disc2.y2", value=np.array([1.0]), units=None),
        Variable(name="functions.x", value=np.array([1.0]), units=None),
        Variable(name="functions.z", value=np.array([5.0, 2.0]), units="m**2"),
        Variable(name="functions.y1", value=np.array([1.0]), units=None),
        Variable(name="functions.y2", value=np.array([1.0]), units=None),
        Variable(name="functions.g1", value=np.array([1.0]), units=None),
        Variable(name="functions.g2", value=np.array([1.0]), units=None),
        Variable(name="functions.f", value=np.array([1.0]), units=None),
    ]
    _test_and_check(problem, False, expected_computed_vars)

    # Check with the whole Sellar problem --------------------------------------
    # WITHOUT promotions, WITH computation
    expected_computed_vars = [
        Variable(name="indeps.x", value=np.array([1.0]), units="Pa"),
        Variable(name="indeps.z", value=np.array([5.0, 2.0]), units="m**2"),
        Variable(name="disc1.x", value=np.array([1.0]), units=None),
        Variable(name="disc1.z", value=np.array([5.0, 2.0]), units="m**2"),
        Variable(name="disc1.y1", value=np.array([25.58830237]), units=None),
        Variable(name="disc1.y2", value=np.array([12.05848815]), units=None),
        Variable(name="disc2.z", value=np.array([5.0, 2.0]), units="m**2"),
        Variable(name="disc2.y1", value=np.array([25.58830237]), units=None),
        Variable(name="disc2.y2", value=np.array([12.05848815]), units=None),
        Variable(name="functions.x", value=np.array([1.0]), units=None),
        Variable(name="functions.z", value=np.array([5.0, 2.0]), units="m**2"),
        Variable(name="functions.y1", value=np.array([25.58830237]), units=None),
        Variable(name="functions.y2", value=np.array([12.05848815]), units=None),
        Variable(name="functions.g1", value=np.array([-22.42830237]), units=None),
        Variable(name="functions.g2", value=np.array([-11.94151185]), units=None),
        Variable(name="functions.f", value=np.array([28.58830817]), units=None),
    ]
    problem.setup()
    problem.run_model()
    _test_and_check(problem, True, expected_vars)
    _test_and_check(problem, False, expected_computed_vars)


def test_variables_from_unconnected_inputs():
    def _test_and_check(
        problem: om.Problem,
        expected_mandatory_vars: List[Variable],
        expected_optional_vars: List[Variable],
    ):
        problem.setup()
        vars = VariableList.from_unconnected_inputs(problem, with_optional_inputs=False)
        assert set(vars) == set(expected_mandatory_vars)

        vars = VariableList.from_unconnected_inputs(problem, with_optional_inputs=True)
        assert set(vars) == set(expected_mandatory_vars + expected_optional_vars)

    # Check with an ExplicitComponent ------------------------------------------
    group = om.Group()
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    problem = om.Problem(group)

    expected_mandatory_vars = [
        Variable(name="x", value=np.array([np.nan]), units=None, is_input=True)
    ]
    expected_optional_vars = [
        Variable(name="z", value=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="y2", value=np.array([1.0]), units=None, is_input=True),
    ]
    _test_and_check(problem, expected_mandatory_vars, expected_optional_vars)

    # Check with a Group -------------------------------------------------------
    group = om.Group()
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])
    problem = om.Problem(group)

    expected_mandatory_vars = [
        Variable(name="x", value=np.array([np.nan]), units=None, is_input=True)
    ]
    expected_optional_vars = [
        Variable(name="z", value=np.array([5.0, 2.0]), units="m**2", is_input=True)
    ]
    _test_and_check(problem, expected_mandatory_vars, expected_optional_vars)

    # Check with the whole Sellar problem --------------------------------------
    # 'z' variable should now be mandatory, because it is so in Functions
    group = om.Group()
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])
    group.add_subsystem("functions", Functions(), promotes=["*"])
    problem = om.Problem(group)

    expected_mandatory_vars = [
        Variable(name="x", value=np.array([np.nan]), units=None, is_input=True),
        Variable(name="z", value=np.array([np.nan, np.nan]), units="m**2", is_input=True),
    ]
    expected_optional_vars = []
    _test_and_check(problem, expected_mandatory_vars, expected_optional_vars)
