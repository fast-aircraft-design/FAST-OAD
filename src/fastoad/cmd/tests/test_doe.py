#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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

import itertools
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from fastoad.openmdao.variables import VariableList

from ..doe import DOEConfig, DOEVariable

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results" / Path(__file__).stem


@pytest.fixture(scope="module")
def cleanup():
    # Reset instance counters before testing
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


@pytest.fixture
def cleanup_doe_variable():
    DOEVariable._id_counter = itertools.count()


@pytest.fixture
def sample_variables():
    """Fixture to create sample DOEVariable instances."""
    var1 = DOEVariable(name="Var1", lower_bound=10.0, upper_bound=20.0)
    var2 = DOEVariable(
        name="Var2",
        lower_bound=5.0,
        upper_bound=15.0,
        reference_value=50,
        name_alias="Var2_pseudo",
    )
    var3 = DOEVariable(name="Var3", bind_variable_to=var1)
    return [var1, var2, var3]


def test_alias_default(cleanup_doe_variable, cleanup):
    """Test that the name_alias defaults to the name."""
    var = DOEVariable(
        name="Var1",
        lower_bound=5,
        upper_bound=15,
    )
    assert var.name_alias == "Var1"


def test_alias_custom(cleanup_doe_variable, cleanup):
    """Test that the name_alias can be set explicitly."""
    var = DOEVariable(
        name="Var1",
        name_alias="custom_alias",
        lower_bound=5,
        upper_bound=15,
    )
    assert var.name_alias == "custom_alias"


def test_missing_bounds_or_binding():
    """Test that a variable without bounds or binding raises ValueError."""
    with pytest.raises(ValueError, match="must either be bound to another variable"):
        DOEVariable(name="var2")


def test_bound_variable_with_direct_bounds():
    """Test that bounds set directly on a bound variable raise a warning."""
    # Create an independent variable to bind to
    var1 = DOEVariable(name="var1", lower_bound=0, upper_bound=10)

    # Create a bound variable and ensure warnings are raised for direct bounds
    with pytest.warns(UserWarning, match="Bounds .* will be ignored"):
        var3 = DOEVariable(name="var3", lower_bound=5, upper_bound=15, bind_variable_to=var1)
        assert var3.lower_bound == var1.lower_bound
        assert var3.upper_bound == var1.upper_bound


def test_invalid_bounds():
    """Test that a variable with invalid bounds (lower > upper) raises ValueError."""
    with pytest.raises(ValueError, match="Invalid DOE bounds for variable"):
        DOEVariable(name="var1", lower_bound=20, upper_bound=10)


def test_invalid_reference_bounds(cleanup_doe_variable, cleanup):
    # Test invalid bounds when a reference value is provided (negative percetage)
    with pytest.raises(ValueError, match="Invalid DOE bounds for variable"):
        DOEVariable(
            name="InvalidReferenceBounds", lower_bound=10, upper_bound=-5, reference_value=50
        )


def test_binding_to_another_variable(cleanup_doe_variable, cleanup):
    # Create a base variable
    base_var = DOEVariable(name="BaseVar", lower_bound=10, upper_bound=20)
    # Bind another variable to it
    bound_var = DOEVariable(name="BoundVar", bind_variable_to=base_var)

    assert bound_var.lower_bound == base_var.lower_bound
    assert bound_var.upper_bound == base_var.upper_bound
    assert bound_var.variable_id == base_var.variable_id


def test_instance_counter_and_id_assignment(cleanup_doe_variable, cleanup):
    var1 = DOEVariable(name="Var1", lower_bound=5, upper_bound=15)
    var2 = DOEVariable(name="Var2", lower_bound=10, upper_bound=20)
    var3 = DOEVariable(name="Var3", bind_variable_to=var1)

    assert var1.variable_id == var3.variable_id
    assert var2.variable_id != var1.variable_id


def test_doe_variable_initialization(cleanup_doe_variable, cleanup, sample_variables):
    """Test initialization of DOEVariable."""
    var1 = sample_variables[0]

    # Test default attributes
    assert var1.name == "Var1"
    assert var1.lower_bound == 10.0
    assert var1.upper_bound == 20.0
    assert var1.reference_value is None
    assert var1.name_alias == "Var1"  # Default to name as pseudo if not provided

    var2 = sample_variables[1]

    # Test reference value logic
    assert var2.name == "Var2"
    assert var2.lower_bound == 47.5
    assert var2.upper_bound == 57.5
    assert var2.reference_value == 50
    assert var2.name_alias == "Var2_pseudo"


def test_doe_config_initialization(cleanup_doe_variable, cleanup, sample_variables):
    """Test initialization of DOEConfig."""
    config = DOEConfig(
        sampling_method="LHS",
        variables=sample_variables,
        destination_folder=RESULTS_FOLDER_PATH,
        sampling_options={"option1": "value1"},
    )

    # Test variable binding and initialization
    assert len(config.variables_binding) == 3
    assert config.variables_binding == [0, 1, 0]  # Assuming the ID values
    assert config.bounds.shape == (2, 2)  # 3 variables, but one is binded


def test_duplicate_variable_warning(
    cleanup_doe_variable,
    cleanup,
):
    """Test that a warning is raised when duplicate variable names are added to DOEConfig."""
    # Define variables with duplicate names
    var1 = DOEVariable(name="var1", lower_bound=0, upper_bound=10)
    var2 = DOEVariable(name="var1", lower_bound=20, upper_bound=30)  # Duplicate name
    var3 = DOEVariable(name="var2", lower_bound=20, upper_bound=30)

    # Create DOEConfig and check for the warning
    with pytest.warns(UserWarning, match="Variable 'var1' set multiple times"):
        config = DOEConfig(
            sampling_method="LHS",
            variables=[var1, var2, var3],
            destination_folder=RESULTS_FOLDER_PATH,
        )

    # Ensure the bounds take precedence for the first variable
    np.testing.assert_array_equal(config.bounds[0], np.asarray([0, 10]))  # Bounds from var1
    assert len(config.bounds) == 2  # var2 is ignored


def test_generate_doe_full_factorial(cleanup_doe_variable, cleanup, sample_variables):
    """Test DOEConfig generate_doe for Full Factorial method."""
    config = DOEConfig(
        sampling_method="Full Factorial",
        variables=sample_variables,
        destination_folder=RESULTS_FOLDER_PATH,
    )

    doe_points = config.sample_doe(sample_count=5)

    # Test that the return type is a list of VariableList instances
    assert isinstance(doe_points, list)
    assert all(isinstance(item, VariableList) for item in doe_points)


def test_generate_doe_random(cleanup_doe_variable, cleanup, sample_variables):
    """Test DOEConfig generate_doe for Random method."""
    config = DOEConfig(
        sampling_method="Random",
        variables=sample_variables,
        destination_folder=RESULTS_FOLDER_PATH,
        seed_value=12,
    )

    doe_points = config.sample_doe(sample_count=5)

    # Test that the return type is a list of VariableList instances
    assert isinstance(doe_points, list)
    assert all(isinstance(item, VariableList) for item in doe_points)


def test_generate_doe_lhs_level_count(cleanup_doe_variable, cleanup, sample_variables):
    """Test DOEConfig generate_doe for LHS method missing level_count."""
    config = DOEConfig(
        sampling_method="LHS",
        variables=sample_variables,
        destination_folder=RESULTS_FOLDER_PATH,
        sampling_options={"level_count": 3, "use_level": 2},
    )

    doe_points = config.sample_doe(sample_count=5)

    # Test that the return type is a list of VariableList instances
    assert isinstance(doe_points, list)
    assert all(isinstance(item, VariableList) for item in doe_points)


def test_write_doe_inputs_single_level(cleanup_doe_variable, cleanup, sample_variables):
    """Test _write_doe_inputs for single-level DOE points using sample variables."""
    destination_folder = RESULTS_FOLDER_PATH / "write_doe_inputs_single_level"
    destination_folder.mkdir(parents=True, exist_ok=True)

    # Create DOEConfig instance with sample_variables and start the sampling
    doe_config = DOEConfig(
        sampling_method="LHS",
        variables=sample_variables,
        destination_folder=destination_folder,
        seed_value=12,
    )
    doe_config.sample_doe(sample_count=5)

    # Act
    doe_config._write_doe_inputs()

    # Assert
    output_file = destination_folder / "DOE_inputs.csv"
    assert output_file.exists(), "The output CSV file was not created."
    written_data = pd.read_csv(output_file, sep=";", quotechar="|")
    expected_data = pd.DataFrame(
        {
            "ID": [0, 1, 2, 3, 4],
            "Var1": [
                19.913898672550232,
                12.526630030370269,
                17.801429708234025,
                14.02914992497084,
                10.308325684759344,
            ],
            "Var2_pseudo": [
                55.77441864271215,
                48.98009939303081,
                50.567478786760596,
                53.56684285525269,
                53.33749401619977,
            ],
            "Var3": [
                19.913898672550232,
                12.526630030370269,
                17.801429708234025,
                14.02914992497084,
                10.308325684759344,
            ],
        }
    ).set_index("ID")
    pd.testing.assert_frame_equal(written_data.set_index("ID"), expected_data)


def test_write_doe_inputs_multilevel(cleanup_doe_variable, cleanup, sample_variables):
    """Test _write_doe_inputs for multi-level DOE points using sample variables."""
    destination_folder = RESULTS_FOLDER_PATH / "write_doe_inputs_multilevel"
    destination_folder.mkdir(parents=True, exist_ok=True)

    test_level = 1

    # Create DOEConfig instance with sample_variables and start the sampling
    doe_config = DOEConfig(
        sampling_method="LHS",
        variables=sample_variables,
        destination_folder=destination_folder,
        seed_value=12,
        sampling_options={"level_count": 3, "use_level": test_level},
    )
    doe_config.sample_doe(sample_count=5)

    # Act
    doe_config._write_doe_inputs()

    # Assert
    output_file = destination_folder / f"DOE_inputs_3D_level{test_level}.csv"

    assert output_file.exists()

    written_data = pd.read_csv(output_file, sep=";", quotechar="|").drop("ID", axis=1)

    expected_data = doe_config.doe_points_df

    # We are not checking using assert_frame_equal because the column name of the output file
    # uses pseudo, while the VariableList returned by sample_doe no
    assert np.allclose(written_data.to_numpy(), expected_data.to_numpy(), atol=1e-4, rtol=1e-4)
