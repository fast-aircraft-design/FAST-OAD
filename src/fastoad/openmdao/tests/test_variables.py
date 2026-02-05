"""
Module for testing VariableList.py
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2025 ONERA & ISAE-SUPAERO
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

from copy import deepcopy
from pathlib import Path

import numpy as np
import openmdao.api as om
import pandas as pd
import pytest
from numpy.testing import assert_allclose
from openmdao.utils.om_warnings import UnitsWarning

import fastoad.models
from fastoad.module_management._plugins import FastoadLoader

from .openmdao_sellar_example.disc1 import Disc1
from .openmdao_sellar_example.disc2 import Disc2
from .openmdao_sellar_example.functions import FunctionF, FunctionG1, FunctionG2
from ..variables import Variable, VariableList


@pytest.fixture(scope="module")
def cleanup():
    # Need to clean up variable descriptions because it is manipulated in other tests.
    Variable.read_variable_descriptions(Path(fastoad.models.__file__).parent, update_existing=False)


def test_variables(with_dummy_plugin_2):
    """Tests features of Variable and VariableList class"""

    # Test description overloading
    FastoadLoader()  # needed to ensure loading of variable description file.
    x = Variable("test:test_variable", val=500)
    assert x.description == "for testing"

    # Initialization
    variables = VariableList()
    a_var = Variable("a", val=0.0)
    b_var = Variable("b", val=1.0)
    n_var = Variable("n", val=np.array(np.nan))
    variables["a"] = {"val": 0.0}  # Tests VariableList.__setitem__ with dict input
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

    assert n_var == Variable("n", val=np.array(np.nan))  # tests __eq__ with nan value

    #   __getitem___
    assert variables["a"] == a_var
    assert variables["b"] is b_var

    #   .names()
    assert list(variables.names()) == ["a", "b"]

    # Tests adding variable with existing name
    assert len(variables) == 2
    assert variables["a"].value == 0.0
    variables.append(Variable("a", val=5.0))
    assert len(variables) == 2
    assert variables["a"].value == 5.0
    variables["a"] = {"value": 42.0}
    assert variables["a"].value == 42.0

    # .update()
    assert len(variables) == 2
    assert list(variables.names()) == ["a", "b"]
    variables.update([n_var], add_variables=False)  # does nothing
    assert len(variables) == 2
    assert list(variables.names()) == ["a", "b"]

    variables.update([n_var], add_variables=True)
    assert len(variables) == 3
    assert list(variables.names()) == ["a", "b", "n"]
    assert variables["a"].value == 42.0

    variables.update(
        [Variable("a", val=-10.0), Variable("not_added", val=0.0)], add_variables=False
    )
    assert len(variables) == 3
    assert list(variables.names()) == ["a", "b", "n"]
    assert variables["a"].value == -10.0

    # We test if descriptions are kept if they exist in the original list but not the new one
    variables.update([Variable("n", desc="description")], add_variables=False)
    assert len(variables) == 3
    assert list(variables.names()) == ["a", "b", "n"]
    assert variables["n"].description == "description"
    variables.update([Variable("n", desc="")], add_variables=False)
    assert len(variables) == 3
    assert list(variables.names()) == ["a", "b", "n"]
    assert variables["n"].description == "description"
    # We test if descriptions are updated if they exist in both lists
    variables.update([Variable("n", desc="new description")], add_variables=False)
    assert len(variables) == 3
    assert list(variables.names()) == ["a", "b", "n"]
    assert variables["n"].description == "new description"


def test_variable_update_missing_metadata():
    """
    Test that Variable.update_missing_metadata only adds missing metadata keys without modifying
    existing ones.
    """
    # Create a source variable with several metadata items
    source_var = Variable(
        "source_var",
        val=10.0,
        units="kg",  # Should be added
        desc="Source variable",
        upper=100.0,
    )

    # Create a target variable with some overlapping and some different metadata
    original_var = Variable(
        "original_var",
        val=20.0,  # Different value
        desc="Target variable",  # Different description
        upper=50.0,  # Different upper bound
        ref=30.0,  # Metadata not in source
        init_metadata=False,
        # Needed because if True (default), the metadata are automatically filled with dummy values
    )

    # Save original values to check they don't change
    original_value = original_var.value
    original_desc = original_var.description
    original_upper = original_var.metadata["upper"]
    original_ref = original_var.metadata["ref"]

    # Apply the update_missing_metadata method
    original_var.update_missing_metadata(source_var)

    # Verify existing metadata was preserved
    assert original_var.value == original_value, "Value should not change"
    assert original_var.description == original_desc, "Description should not change"
    assert original_var.metadata["upper"] == original_upper, "Upper bound should not change"
    assert original_var.metadata["ref"] == original_ref, "Ref should not change"
    assert "units" in original_var.metadata, "units should be added"
    assert original_var.metadata["units"] == source_var.metadata["units"], (
        "Units should match source"
    )

    # Create a variable with no metadata to update from
    empty_var = Variable("empty_var", val=5.0, init_metadata=False)
    original_metadata_count = len(original_var.metadata)

    # Apply the update_missing_metadata with an empty variable
    original_var.update_missing_metadata(empty_var)
    assert len(original_var.metadata) == original_metadata_count, "No new metadata should be added"


def test_update_with_no_init_metadata_variables():
    """Test updating variable list with variables created with init_metadata=False."""
    # Create variables with standard metadata initialization
    var1 = Variable("var1", val=10.0, units="m", desc="Description for var1")
    var2 = Variable("var2", val=20.0, units="kg", desc="Description for var2")
    var3 = Variable("var3", val=30.0, units="s", desc="Description for var3")
    standard_var_list = VariableList([var1, var2, var3])

    # Create variables without metadata initialization
    no_meta_var1 = Variable(
        "var1", val=15.0, units="ft", desc="Updated description for var1", init_metadata=False
    )
    no_meta_var2 = Variable("var2", val=25.0, units="lb", init_metadata=False)  # No description
    no_meta_var4 = Variable(
        "var4", val=40.0, units="K", desc="Description for var4", init_metadata=False
    )
    no_meta_var_list = VariableList([no_meta_var1, no_meta_var2, no_meta_var4])

    # Update with default parameters (add_variables=True, merge_metadata=False)
    test_var_list = deepcopy(standard_var_list)
    test_var_list.update(no_meta_var_list)

    # Check that values and metadata were updated
    assert test_var_list["var1"].value == 15.0
    assert test_var_list["var1"].units == "ft"
    assert test_var_list["var1"].description == "Updated description for var1"

    # Check that description is preserved when no description is provided
    assert test_var_list["var2"].value == 25.0
    assert test_var_list["var2"].units == "lb"
    assert test_var_list["var2"].description == "Description for var2"

    # Check that new variable was added
    assert "var4" in test_var_list.names()
    assert test_var_list["var4"].value == 40.0
    assert test_var_list["var4"].units == "K"

    # Check that var3 is unchanged
    assert test_var_list["var3"].value == 30.0
    assert test_var_list["var3"].units == "s"


def test_update_with_no_init_metadata_and_merge_metadata():
    """Test the merge_metadata parameter with variables created with init_metadata=False."""
    # Create a variable with rich metadata
    rich_var = Variable(
        "var1",
        val=10.0,
        units="m",
        desc="Rich description",
        upper=200.0,
        lower=0.0,
        tags={"tag1", "tag2"},
    )
    rich_var_list = VariableList([rich_var])

    # Save original metadata keys for later comparison
    original_metadata_keys = set(rich_var.metadata.keys())

    # Create a variable with minimal metadata (init_metadata=False)
    minimal_var = Variable("var1", val=15.0, init_metadata=False)
    minimal_var_list = VariableList([minimal_var])

    # Case 1: Update with merge_metadata=False (default)
    test_var_list_no_fill = deepcopy(rich_var_list)
    test_var_list_no_fill.update(minimal_var_list)

    # Check that values were updated
    assert test_var_list_no_fill["var1"].value == 15.0
    # Description should be preserved since minimal_var has no description
    assert test_var_list_no_fill["var1"].description == "Rich description"

    # With merge_metadata=False, metadata like units, lower should be lost
    updated_metadata_keys = set(test_var_list_no_fill["var1"].metadata.keys())
    assert "units" not in updated_metadata_keys
    assert "lower" not in updated_metadata_keys

    # Case 2: Update with merge_metadata=True
    test_var_list_with_fill = deepcopy(rich_var_list)
    test_var_list_with_fill.update(minimal_var_list, merge_metadata=True)

    # Check that values were updated
    assert test_var_list_with_fill["var1"].value == 15.0
    assert test_var_list_with_fill["var1"].description == "Rich description"

    # With merge_metadata=True, all metadata should be preserved
    filled_metadata_keys = set(test_var_list_with_fill["var1"].metadata.keys())

    # All original keys should still be present
    for key in original_metadata_keys:
        assert key in filled_metadata_keys

    # Check specific metadata values are preserved
    assert test_var_list_with_fill["var1"].metadata["upper"] == 200.0
    assert test_var_list_with_fill["var1"].metadata["lower"] == 0.0
    assert "tag1" in test_var_list_with_fill["var1"].metadata["tags"]
    assert "tag2" in test_var_list_with_fill["var1"].metadata["tags"]

    # Test a variable list with multiple variables
    var1 = Variable("var1", val=10.0, tags={"tag1", "tag2"}, units="m", desc="Description for var1")
    var2 = Variable("var2", val=20.0, units="kg", desc="Description for var2")
    var_list = VariableList([var1, var2])

    no_meta_var1 = Variable("var1", val=15.0, units="ft", init_metadata=False)
    no_meta_var2 = Variable("var2", val=25.0, desc="New description", init_metadata=False)
    no_meta_var_list = VariableList([no_meta_var1, no_meta_var2])

    # Update with merge_metadata=True
    var_list.update(no_meta_var_list, merge_metadata=True)

    # Check results
    assert var_list["var1"].value == 15.0
    assert var_list["var1"].units == "ft"
    assert var_list["var1"].metadata["tags"] == {"tag1", "tag2"}  # Preserved
    assert var_list["var1"].description == "Description for var1"  # Preserved

    assert var_list["var2"].value == 25.0
    assert var_list["var2"].units == "kg"  # Preserved
    assert var_list["var2"].description == "New description"  # Updated


def test_ivc_from_to_variables():
    """
    Tests VariableList.to_ivc() and VariableList.from_ivc()
    """
    variables = VariableList()
    variables["a"] = {"value": 5}
    variables["b"] = {"value": 2.5, "units": "m"}
    variables["c"] = {"value": -3.2, "units": "kg/s", "desc": "some test"}

    ivc = variables.to_ivc()
    problem = om.Problem(reports=False)
    problem.model.add_subsystem("ivc", ivc, promotes=["*"])
    problem.setup()
    assert problem["a"] == 5
    assert problem["b"] == 2.5
    assert problem.get_val("b", units="cm") == 250
    assert problem.get_val("c", units="kg/ms") == -0.0032

    ivc = variables.to_ivc()
    new_variables = VariableList.from_ivc(ivc)
    assert variables.names() == new_variables.names()
    for var, new_var in zip(variables, new_variables):
        assert var == new_var


def test_df_from_to_variables():
    """
    Tests VariableList.to_dataframe() and VariableList.from_dataframe()
    """
    variables = VariableList()
    variables["a"] = {"val": 5}
    variables["b"] = {"val": np.array([1.0, 2.0, 3.0]), "units": "m"}
    variables["c"] = {"val": [1.0, 2.0, 3.0], "units": "kg/s", "desc": "some test"}
    variables["d"] = {"val": "my value is a string"}

    df = variables.to_dataframe()
    assert np.all(df["name"] == ["a", "b", "c", "d"])
    assert np.all(
        df["val"]
        == pd.Series(name="val", data=[5, [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], "my value is a string"])
    )  # There is a need for Series in the right term because of the non-homogeneous shape.
    assert np.all(df["units"].to_list() == [None, "m", "kg/s", None])
    assert np.all(df["desc"].to_list() == ["", "", "some test", ""])

    new_variables = VariableList.from_dataframe(df)

    assert variables.names() == new_variables.names()
    for var, new_var in zip(variables, new_variables):
        assert var == new_var


def _compare_variable_lists(variables: list[Variable], expected_variables: list[Variable]):
    def sort_key(v):
        return v.name

    variables.sort(key=sort_key)
    expected_variables.sort(key=sort_key)
    assert variables == expected_variables

    # is_input is willingly ignored when checking equality of variables, but here, we want to
    # test it.
    variables_dict = {var.name: var.is_input for var in variables}
    expected_variables_dict = {var.name: var.is_input for var in expected_variables}
    assert variables_dict == expected_variables_dict

    variables_dict = {var.name: var.description for var in variables}
    expected_variables_dict = {var.name: var.description for var in expected_variables}
    assert variables_dict == expected_variables_dict


def test_get_variables_from_problem_with_an_explicit_component():
    problem = om.Problem(reports=False)
    problem.model.add_subsystem("disc1", Disc1(), promotes=["*"])

    variables_before_setup = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True
    )
    problem.setup()
    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True
    )
    assert variables_before_setup == variables

    expected_variables = [
        Variable(name="x", val=np.array([np.nan]), units=None, desc="input x", is_input=True),
        Variable(name="y2", val=np.array([1.0]), units=None, is_input=True, desc="variable y2"),
        Variable(name="z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="y1", val=np.array([1.0]), units=None, is_input=False, desc="variable y1"),
    ]

    _compare_variable_lists(variables, expected_variables)


def test_get_variables_from_problem_with_a_group():
    group = om.Group()
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])
    problem = om.Problem(group, reports=False)
    variables_before_setup = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True
    )
    problem.setup()
    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True
    )
    assert variables_before_setup == variables

    expected_variables = [
        Variable(name="x", val=np.array([np.nan]), units=None, is_input=True, desc="input x"),
        Variable(name="y1", val=np.array([1.0]), units=None, is_input=False, desc="variable y1"),
        Variable(name="y2", val=np.array([1.0]), units=None, is_input=False, desc="variable y2"),
        Variable(
            name="z", val=np.array([5.0, 2.0]), units="m**2", is_input=True, desc="variable z"
        ),
    ]

    _compare_variable_lists(variables, expected_variables)


def test_get_variables_from_problem_sellar_with_promotion_without_computation():
    group = om.Group()
    indeps = group.add_subsystem("indeps", om.IndepVarComp(), promotes=["*"])
    indeps.add_output("x", 1.0, units="Pa")  # This setting of units will prevail in our output
    indeps.add_output("z", [5.0, 2.0], units="m**2")
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])
    group.add_subsystem("objective", FunctionF(), promotes=["*"])
    group.add_subsystem("constraint1", FunctionG1(), promotes=["*"])
    group.add_subsystem("constraint2", FunctionG2(), promotes=["*"])
    group.nonlinear_solver = om.NonlinearBlockGS()
    problem = om.Problem(group, reports=False)
    with pytest.warns(UnitsWarning):
        problem.setup()
        problem.final_setup()

    expected_variables_promoted = [
        Variable(name="x", val=np.array([1.0]), units="Pa", is_input=True, desc="input x"),
        Variable(
            name="z", val=np.array([5.0, 2.0]), units="m**2", is_input=True, desc="variable z"
        ),
        Variable(name="y1", val=np.array([1.0]), units=None, is_input=False, desc="variable y1"),
        Variable(name="y2", val=np.array([1.0]), units=None, is_input=False, desc="variable y2"),
        Variable(name="g1", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="g2", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="f", val=np.array([1.0]), units=None, is_input=False),
    ]
    expected_variables_non_promoted = [
        Variable(name="indeps.x", val=np.array([1.0]), units="Pa", is_input=True),
        Variable(name="indeps.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="disc1.x", val=np.array([np.nan]), units=None, is_input=True, desc="input x"),
        Variable(name="disc1.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(
            name="disc1.y1", val=np.array([1.0]), units=None, is_input=False, desc="variable y1"
        ),
        Variable(
            name="disc1.y2", val=np.array([1.0]), units=None, is_input=True, desc="variable y2"
        ),
        Variable(
            name="disc2.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True, desc="variable z"
        ),
        Variable(name="disc2.y1", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="disc2.y2", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="objective.x", val=np.array([2]), units=None, is_input=True),
        Variable(name="objective.z", val=np.array([np.nan, np.nan]), units="m**2", is_input=True),
        Variable(name="objective.y1", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="objective.y2", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="objective.f", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="constraint1.y1", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="constraint1.g1", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="constraint2.y2", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="constraint2.g2", val=np.array([1.0]), units=None, is_input=False),
    ]

    variables = VariableList.from_problem(problem, use_initial_values=True, get_promoted_names=True)
    _compare_variable_lists(variables, expected_variables_promoted)

    variables = VariableList.from_problem(
        problem, use_initial_values=True, get_promoted_names=False
    )
    _compare_variable_lists(variables, expected_variables_non_promoted)

    # use_initial_values=False should have no effect while problem has not been run
    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True
    )
    _compare_variable_lists(variables, expected_variables_promoted)

    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=False
    )
    _compare_variable_lists(variables, expected_variables_non_promoted)


def test_get_variables_from_problem_sellar_with_promotion_with_computation():
    group = om.Group()
    indeps = group.add_subsystem("indeps", om.IndepVarComp(), promotes=["*"])
    indeps.add_output("x", 1.0, units="Pa")  # This setting of units will prevail in our output
    indeps.add_output("z", [5.0, 2.0], units="m**2")
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])
    group.add_subsystem("objective", FunctionF(), promotes=["*"])
    group.add_subsystem("constraint1", FunctionG1(), promotes=["*"])
    group.add_subsystem("constraint2", FunctionG2(), promotes=["*"])
    group.nonlinear_solver = om.NonlinearBlockGS()
    problem = om.Problem(group, reports=False)
    with pytest.warns(UnitsWarning):
        problem.setup()
        problem.final_setup()

    expected_variables_promoted_initial = [
        Variable(name="x", val=np.array([1.0]), units="Pa", is_input=True, desc="input x"),
        Variable(
            name="z", val=np.array([5.0, 2.0]), units="m**2", is_input=True, desc="variable z"
        ),
        Variable(name="y1", val=np.array([1.0]), units=None, is_input=False, desc="variable y1"),
        Variable(name="y2", val=np.array([1.0]), units=None, is_input=False, desc="variable y2"),
        Variable(name="g1", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="g2", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="f", val=np.array([1.0]), units=None, is_input=False),
    ]
    expected_variables_promoted_computed = [
        Variable(name="x", val=np.array([1.0]), units="Pa", is_input=True, desc="input x"),
        Variable(
            name="z", val=np.array([5.0, 2.0]), units="m**2", is_input=True, desc="variable z"
        ),
        Variable(
            name="y1", val=np.array([25.58830237]), units=None, is_input=False, desc="variable y1"
        ),
        Variable(
            name="y2", val=np.array([12.05848815]), units=None, is_input=False, desc="variable y2"
        ),
        Variable(name="f", val=np.array([28.58830817]), units=None, is_input=False),
        Variable(name="g1", val=np.array([-22.42830237]), units=None, is_input=False),
        Variable(name="g2", val=np.array([-11.94151185]), units=None, is_input=False),
    ]
    expected_variables_non_promoted_initial = [
        Variable(name="indeps.x", val=np.array([1.0]), units="Pa", is_input=True),
        Variable(name="indeps.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="disc1.x", val=np.array([np.nan]), units=None, is_input=True, desc="input x"),
        Variable(name="disc1.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(
            name="disc1.y1", val=np.array([1.0]), units=None, is_input=False, desc="variable y1"
        ),
        Variable(
            name="disc1.y2", val=np.array([1.0]), units=None, is_input=True, desc="variable y2"
        ),
        Variable(
            name="disc2.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True, desc="variable z"
        ),
        Variable(name="disc2.y1", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="disc2.y2", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="objective.x", val=np.array([2]), units=None, is_input=True),
        Variable(name="objective.z", val=np.array([np.nan, np.nan]), units="m**2", is_input=True),
        Variable(name="objective.y1", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="objective.y2", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="objective.f", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="constraint1.y1", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="constraint1.g1", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="constraint2.y2", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="constraint2.g2", val=np.array([1.0]), units=None, is_input=False),
    ]
    expected_variables_non_promoted_computed = [
        Variable(name="indeps.x", val=np.array([1.0]), units="Pa", is_input=True),
        Variable(name="indeps.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="disc1.x", val=np.array([1.0]), units=None, is_input=True, desc="input x"),
        Variable(name="disc1.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(
            name="disc1.y1",
            val=np.array([25.58830237]),
            units=None,
            is_input=False,
            desc="variable y1",
        ),
        Variable(
            name="disc1.y2",
            val=np.array([12.05848815]),
            units=None,
            is_input=True,
            desc="variable y2",
        ),
        Variable(
            name="disc2.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True, desc="variable z"
        ),
        Variable(name="disc2.y1", val=np.array([25.58830237]), units=None, is_input=True),
        Variable(name="disc2.y2", val=np.array([12.05848815]), units=None, is_input=False),
        Variable(name="objective.x", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="objective.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="objective.y1", val=np.array([25.58830237]), units=None, is_input=True),
        Variable(name="objective.y2", val=np.array([12.05848815]), units=None, is_input=True),
        Variable(name="objective.f", val=np.array([28.58830817]), units=None, is_input=False),
        Variable(name="constraint1.y1", val=np.array([25.58830237]), units=None, is_input=True),
        Variable(name="constraint1.g1", val=np.array([-22.42830237]), units=None, is_input=False),
        Variable(name="constraint2.y2", val=np.array([12.05848815]), units=None, is_input=True),
        Variable(name="constraint2.g2", val=np.array([-11.94151185]), units=None, is_input=False),
    ]

    problem.run_model()

    variables = VariableList.from_problem(problem, use_initial_values=True, get_promoted_names=True)
    _compare_variable_lists(variables, expected_variables_promoted_initial)

    variables = VariableList.from_problem(
        problem, use_initial_values=True, get_promoted_names=False
    )
    _compare_variable_lists(variables, expected_variables_non_promoted_initial)

    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True
    )
    _compare_variable_lists(variables, expected_variables_promoted_computed)

    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=False
    )
    _compare_variable_lists(variables, expected_variables_non_promoted_computed)


def test_get_variables_from_problem_sellar_without_promotion_without_computation():
    group = om.Group()
    indeps = group.add_subsystem("indeps", om.IndepVarComp())
    indeps.add_output("x", 1.0)
    indeps.add_output("z", [5.0, 2.0], units="m**2")
    group.add_subsystem("disc2", Disc2())
    group.add_subsystem("disc1", Disc1())
    group.add_subsystem("objective", FunctionF())
    group.add_subsystem("constraint1", FunctionG1())
    group.add_subsystem("constraint2", FunctionG2())
    group.nonlinear_solver = om.NonlinearBlockGS()
    group.connect("indeps.x", ["disc1.x", "objective.x"])
    group.connect("indeps.z", ["disc1.z", "disc2.z", "objective.z"])
    group.connect("disc1.y1", ["disc2.y1", "objective.y1", "constraint1.y1"])
    group.connect("disc2.y2", ["disc1.y2", "objective.y2", "constraint2.y2"])

    problem = om.Problem(group, reports=False)
    problem.setup()
    problem.final_setup()

    expected_variables_initial = [
        Variable(name="indeps.x", val=np.array([1.0]), is_input=True),
        Variable(name="indeps.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="disc1.x", val=np.array([np.nan]), units=None, is_input=True, desc="input x"),
        Variable(name="disc1.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(
            name="disc1.y1", val=np.array([1.0]), units=None, is_input=False, desc="variable y1"
        ),
        Variable(
            name="disc1.y2", val=np.array([1.0]), units=None, is_input=True, desc="variable y2"
        ),
        Variable(
            name="disc2.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True, desc="variable z"
        ),
        Variable(name="disc2.y1", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="disc2.y2", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="objective.x", val=np.array([2]), units=None, is_input=True),
        Variable(name="objective.z", val=np.array([np.nan, np.nan]), units="m**2", is_input=True),
        Variable(name="objective.y1", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="objective.y2", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="objective.f", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="constraint1.y1", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="constraint1.g1", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="constraint2.y2", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="constraint2.g2", val=np.array([1.0]), units=None, is_input=False),
    ]

    variables = VariableList.from_problem(
        problem, use_initial_values=True, get_promoted_names=True, promoted_only=True
    )
    _compare_variable_lists(variables, [])

    variables = VariableList.from_problem(
        problem, use_initial_values=True, get_promoted_names=True, promoted_only=False
    )
    _compare_variable_lists(variables, expected_variables_initial)

    variables = VariableList.from_problem(
        problem, use_initial_values=True, get_promoted_names=False, promoted_only=False
    )
    _compare_variable_lists(variables, expected_variables_initial)

    # use_initial_values=False should have no effect while problem has not been run
    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True, promoted_only=True
    )
    _compare_variable_lists(variables, [])

    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True, promoted_only=False
    )
    _compare_variable_lists(variables, expected_variables_initial)

    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=False, promoted_only=False
    )
    _compare_variable_lists(variables, expected_variables_initial)


def test_get_variables_from_problem_sellar_without_promotion_with_computation():
    group = om.Group()
    indeps = group.add_subsystem("indeps", om.IndepVarComp())
    indeps.add_output("x", 1.0)
    indeps.add_output("z", [5.0, 2.0], units="m**2")
    group.add_subsystem("disc2", Disc2())
    group.add_subsystem("disc1", Disc1())
    group.add_subsystem("objective", FunctionF())
    group.add_subsystem("constraint1", FunctionG1())
    group.add_subsystem("constraint2", FunctionG2())
    group.nonlinear_solver = om.NonlinearBlockGS()
    group.connect("indeps.x", ["disc1.x", "objective.x"])
    group.connect("indeps.z", ["disc1.z", "disc2.z", "objective.z"])
    group.connect("disc1.y1", ["disc2.y1", "objective.y1", "constraint1.y1"])
    group.connect("disc2.y2", ["disc1.y2", "objective.y2", "constraint2.y2"])

    problem = om.Problem(group, reports=False)
    problem.setup()

    expected_variables_initial = [
        Variable(name="indeps.x", val=np.array([1.0]), is_input=True),
        Variable(name="indeps.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="disc1.x", val=np.array([np.nan]), units=None, is_input=True, desc="input x"),
        Variable(name="disc1.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(
            name="disc1.y1", val=np.array([1.0]), units=None, is_input=False, desc="variable y1"
        ),
        Variable(
            name="disc1.y2", val=np.array([1.0]), units=None, is_input=True, desc="variable y2"
        ),
        Variable(
            name="disc2.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True, desc="variable z"
        ),
        Variable(name="disc2.y1", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="disc2.y2", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="objective.x", val=np.array([2]), units=None, is_input=True),
        Variable(name="objective.z", val=np.array([np.nan, np.nan]), units="m**2", is_input=True),
        Variable(name="objective.y1", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="objective.y2", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="objective.f", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="constraint1.y1", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="constraint1.g1", val=np.array([1.0]), units=None, is_input=False),
        Variable(name="constraint2.y2", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="constraint2.g2", val=np.array([1.0]), units=None, is_input=False),
    ]
    expected_variables_computed = [
        Variable(name="indeps.x", val=np.array([1.0]), is_input=True),
        Variable(name="indeps.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="disc1.x", val=np.array([1.0]), units=None, is_input=True, desc="input x"),
        Variable(name="disc1.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(
            name="disc1.y1",
            val=np.array([25.58830237]),
            units=None,
            is_input=False,
            desc="variable y1",
        ),
        Variable(
            name="disc1.y2",
            val=np.array([12.05848815]),
            units=None,
            is_input=True,
            desc="variable y2",
        ),
        Variable(
            name="disc2.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True, desc="variable z"
        ),
        Variable(name="disc2.y1", val=np.array([25.58830237]), units=None, is_input=True),
        Variable(name="disc2.y2", val=np.array([12.05848815]), units=None, is_input=False),
        Variable(name="objective.x", val=np.array([1.0]), units=None, is_input=True),
        Variable(name="objective.z", val=np.array([5.0, 2.0]), units="m**2", is_input=True),
        Variable(name="objective.y1", val=np.array([25.58830237]), units=None, is_input=True),
        Variable(name="objective.y2", val=np.array([12.05848815]), units=None, is_input=True),
        Variable(name="objective.f", val=np.array([28.58830817]), units=None, is_input=False),
        Variable(name="constraint1.y1", val=np.array([25.58830237]), units=None, is_input=True),
        Variable(name="constraint2.y2", val=np.array([12.05848815]), units=None, is_input=True),
        Variable(name="constraint1.g1", val=np.array([-22.42830237]), units=None, is_input=False),
        Variable(name="constraint2.g2", val=np.array([-11.94151185]), units=None, is_input=False),
    ]
    problem.run_model()

    variables = VariableList.from_problem(
        problem, use_initial_values=True, get_promoted_names=True, promoted_only=True
    )
    _compare_variable_lists(variables, [])

    variables = VariableList.from_problem(
        problem, use_initial_values=True, get_promoted_names=True, promoted_only=False
    )
    _compare_variable_lists(variables, expected_variables_initial)

    variables = VariableList.from_problem(
        problem, use_initial_values=True, get_promoted_names=False, promoted_only=False
    )
    _compare_variable_lists(variables, expected_variables_initial)

    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True, promoted_only=False
    )
    _compare_variable_lists(variables, expected_variables_computed)

    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=False, promoted_only=False
    )
    _compare_variable_lists(variables, expected_variables_computed)


pytestmark = pytest.mark.filterwarnings(
    "ignore:Call to deprecated class method from_unconnected_inputs",
    "ignore:Call to deprecated function \(or staticmethod\) get_unconnected_input_names",
)


def _test_and_check_from_unconnected_inputs(
    problem: om.Problem,
    expected_mandatory_variables: list[Variable],
    expected_optional_variables: list[Variable],
):
    problem.setup()
    problem.final_setup()
    variables = VariableList.from_unconnected_inputs(problem, with_optional_inputs=False)
    assert set(variables) == set(expected_mandatory_variables)

    variables_dict = {var.name: var.description for var in variables}
    expected_variables_dict = {var.name: var.description for var in expected_mandatory_variables}
    assert variables_dict == expected_variables_dict

    variables = VariableList.from_unconnected_inputs(problem, with_optional_inputs=True)
    assert set(variables) == set(expected_mandatory_variables + expected_optional_variables)

    variables_dict = {var.name: var.description for var in variables}
    expected_variables_dict = {
        var.name: var.description
        for var in (expected_mandatory_variables + expected_optional_variables)
    }
    assert variables_dict == expected_variables_dict


def test_variables_from_unconnected_inputs_with_an_explicit_component():
    group = om.Group()
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    problem = om.Problem(group, reports=False)

    expected_mandatory_variables = [
        Variable(
            name="x",
            val=np.array([np.nan]),
            units=None,
            is_input=True,
            prom_name="x",
            desc="input x",
        )
    ]
    expected_optional_variables = [
        Variable(name="z", val=np.array([5.0, 2.0]), units="m**2", is_input=True, prom_name="z"),
        Variable(
            name="y2",
            val=np.array([1.0]),
            units=None,
            is_input=True,
            prom_name="y2",
            desc="variable y2",
        ),
    ]
    _test_and_check_from_unconnected_inputs(
        problem, expected_mandatory_variables, expected_optional_variables
    )


def test_variables_from_unconnected_inputs_with_a_group(cleanup):
    group = om.Group()
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])
    problem = om.Problem(group, reports=False)

    expected_mandatory_variables = [
        Variable(
            name="x",
            val=np.array([np.nan]),
            units=None,
            is_input=True,
            prom_name="x",
            desc="input x",
        )
    ]
    expected_optional_variables = [
        Variable(
            name="z",
            val=np.array([5.0, 2.0]),
            units="m**2",
            is_input=True,
            prom_name="z",
            desc="variable z",
        )
    ]
    _test_and_check_from_unconnected_inputs(
        problem, expected_mandatory_variables, expected_optional_variables
    )


def test_variables_from_unconnected_inputs_with_sellar_problem(cleanup):
    # 'z' variable should now be mandatory, because it is so in Functions
    group = om.Group()
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])
    group.add_subsystem("objective", FunctionF(), promotes=["*"])
    group.add_subsystem("constaint1", FunctionG1(), promotes=["*"])
    group.add_subsystem("constaint2", FunctionG2(), promotes=["*"])
    problem = om.Problem(group, reports=False)

    expected_mandatory_variables = [
        Variable(
            name="x",
            val=np.array([np.nan]),
            units=None,
            is_input=True,
            prom_name="x",
            desc="input x",
        ),
        Variable(
            name="z", val=np.array([np.nan, np.nan]), units="m**2", is_input=True, prom_name="z"
        ),
    ]
    # Pseudo optional variable 'z' is optional in Disc1/2 but mandatory in Functions but description
    # is provided in Disc2. We test here that if the kwarg "with_optional_inputs" is true the
    # description of the variable is updated.

    expected_optional_variables = [
        Variable(
            name="z",
            value=np.array([np.nan, np.nan]),
            units="m**2",
            is_input=True,
            prom_name="z",
            desc="variable z",
        )
    ]
    _test_and_check_from_unconnected_inputs(
        problem, expected_mandatory_variables, expected_optional_variables
    )


def test_get_variables_from_problem_sellar_with_promotion_and_connect():
    group = om.Group()
    indeps = group.add_subsystem("indeps", om.IndepVarComp(), promotes=["*"])
    indeps.add_output("indep:x", 1.0)
    indeps.add_output("z", [5.0, 2.0], units="m**2")
    group.add_subsystem("disc1", Disc1(), promotes=["x", "z"])
    group.add_subsystem("disc2", Disc2(), promotes=["z"])
    group.add_subsystem("objective", FunctionF(), promotes=["*"])
    group.add_subsystem("constaint1", FunctionG1(), promotes=["*"])
    group.add_subsystem("constaint2", FunctionG2(), promotes=["*"])

    # Connections
    group.connect("indep:x", "x")
    group.connect("disc1.y1", "disc2.y1")
    group.connect("disc2.y2", "disc1.y2")
    group.connect("disc1.y1", "y1")
    group.connect("disc2.y2", "y2")

    problem = om.Problem(group, reports=False)
    variables_before_setup = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True
    )
    problem.setup()
    problem.final_setup()
    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True
    )
    assert variables_before_setup == variables

    # x should be an output
    assert not variables["x"].is_input
    # y1 and y2 should be outputs
    assert not variables["y1"].is_input
    assert not variables["y2"].is_input
    # f, g1 and g2 should be outputs
    assert not variables["f"].is_input
    assert not variables["g1"].is_input
    assert not variables["g2"].is_input
    # indep:x and z as indeps should be inputs
    assert variables["indep:x"].is_input
    assert variables["z"].is_input

    # Test for io_status
    # Check that all variables are returned
    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True, io_status="all"
    )

    assert "y1" in variables.names()
    assert "y2" in variables.names()
    assert "f" in variables.names()
    assert "g1" in variables.names()
    assert "g2" in variables.names()
    assert "x" in variables.names()
    assert "indep:x" in variables.names()
    assert "z" in variables.names()

    # Check that only inputs are returned
    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True, io_status="inputs"
    )

    assert "y1" not in variables.names()
    assert "y2" not in variables.names()
    assert "f" not in variables.names()
    assert "g1" not in variables.names()
    assert "g2" not in variables.names()
    assert "indep:x" in variables.names()
    assert "z" in variables.names()

    # Check that only outputs are returned
    variables = VariableList.from_problem(
        problem, use_initial_values=False, get_promoted_names=True, io_status="outputs"
    )

    assert "y1" in variables.names()
    assert "y2" in variables.names()
    assert "f" in variables.names()
    assert "g1" in variables.names()
    assert "g2" in variables.names()
    assert "x" in variables.names()
    assert "indep:x" not in variables.names()
    assert "z" not in variables.names()


def test_get_val():
    variables = VariableList()
    variables["bar"] = {"value": 1.0, "units": "m"}
    variables["baq"] = {"value": np.array([1.0])}
    variables["foo"] = {"value": 1.0, "units": "m**2"}
    variables["baz"] = {"value": [1.0, 2.0], "units": "m"}
    variables["bat"] = {"value": (1.0, 2.0), "units": "m"}
    variables["qux"] = {"value": np.array([1.0, 2.0]), "units": "m"}
    variables["quux"] = {"value": [[1.0, 2.0], [2.0, 3.0]], "units": "m"}
    data = variables["bar"].get_val()
    assert not isinstance(data, list) and not isinstance(data, np.ndarray)
    assert_allclose(data, 1, rtol=1e-3, atol=1e-5)
    units = "km"
    data = variables["bar"].get_val(new_units=units)
    assert_allclose(data, 1e-3, rtol=1e-3, atol=1e-5)
    data = variables["baq"].get_val()
    assert not isinstance(data, list) and not isinstance(data, np.ndarray)
    assert_allclose(data, 1, rtol=1e-3, atol=1e-5)
    with pytest.raises(TypeError):
        data = variables["foo"].get_val(new_units=units)
    data = variables["baz"].get_val(new_units=units)
    assert_allclose(data, [1e-3, 2e-3], rtol=1e-3, atol=1e-5)
    data = variables["bat"].get_val(new_units=units)
    assert_allclose(data, [1e-3, 2e-3], rtol=1e-3, atol=1e-5)
    data = variables["qux"].get_val(new_units=units)
    assert_allclose(data, [1e-3, 2e-3], rtol=1e-3, atol=1e-5)
    data = variables["quux"].get_val(new_units=units)
    assert_allclose(data, [[1e-3, 2e-3], [2e-3, 3e-3]], rtol=1e-3, atol=1e-5)
