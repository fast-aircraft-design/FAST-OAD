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


@pytest.fixture()
def cleanup_DOEVariable():
    DOEVariable._instance_counter = 0
    DOEVariable._next_instance = -1


@pytest.fixture
def sample_variables():
    """Fixture to create sample DOEVariable instances."""
    var1 = DOEVariable(name="Var1", bound_lower=10.0, bound_upper=20.0)
    var2 = DOEVariable(
        name="Var2",
        bound_lower=5.0,
        bound_upper=15.0,
        reference_value=50,
        name_pseudo="Var2_pseudo",
    )
    var3 = DOEVariable(name="Var3", bind_variable_to=var1)
    return [var1, var2, var3]


def test_invalid_bounds(cleanup_DOEVariable, cleanup):
    # Test invalid bounds without reference value (lower>upper)
    with pytest.raises(ValueError):
        DOEVariable(name="InvalidBounds", bound_lower=20, bound_upper=10)


def test_invalid_reference_bounds(cleanup_DOEVariable, cleanup):
    # Test invalid bounds when a reference value is provided (negative percetage)
    with pytest.raises(ValueError):
        DOEVariable(
            name="InvalidReferenceBounds", bound_lower=10, bound_upper=-5, reference_value=50
        )


def test_binding_to_another_variable(cleanup_DOEVariable, cleanup):
    # Create a base variable
    base_var = DOEVariable(name="BaseVar", bound_lower=10, bound_upper=20)
    # Bind another variable to it
    bound_var = DOEVariable(name="BoundVar", bind_variable_to=base_var)

    assert bound_var.bound_lower == base_var.bound_lower
    assert bound_var.bound_upper == base_var.bound_upper
    assert bound_var.id_variable == base_var.id_variable


def test_instance_counter_and_id_assignment(cleanup_DOEVariable, cleanup):
    var1 = DOEVariable(name="Var1", bound_lower=5, bound_upper=15)
    var2 = DOEVariable(name="Var2", bound_lower=10, bound_upper=20)
    var3 = DOEVariable(name="Var3", bound_lower=15, bound_upper=25, bind_variable_to=var1)

    assert var1.id_variable == 0
    assert var2.id_variable == 1
    assert var3.id_variable == 0  # Bound to var1
    assert DOEVariable._instance_counter == 3  # Three instances created


def test_doe_variable_initialization(cleanup_DOEVariable, cleanup, sample_variables):
    """Test initialization of DOEVariable."""
    var1 = sample_variables[0]

    # Test default attributes
    assert var1.name == "Var1"
    assert var1.bound_lower == 10.0
    assert var1.bound_upper == 20.0
    assert var1.reference_value is None
    assert var1.name_pseudo == "Var1"  # Default to name as pseudo if not provided

    var2 = sample_variables[1]

    # Test reference value logic
    assert var2.name == "Var2"
    assert var2.bound_lower == 47.5
    assert var2.bound_upper == 57.5
    assert var2.reference_value == 50
    assert var2.name_pseudo == "Var2_pseudo"


def test_doe_config_initialization(cleanup_DOEVariable, cleanup, sample_variables):
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


def test_generate_doe_full_factorial(cleanup_DOEVariable, cleanup, sample_variables):
    """Test DOEConfig generate_doe for Full Factorial method."""
    config = DOEConfig(
        sampling_method="Full Factorial",
        variables=sample_variables,
        destination_folder=RESULTS_FOLDER_PATH,
    )

    doe_points = config.sampling_doe(sample_count=5)

    # Test that the return type is a list of VariableList instances
    assert isinstance(doe_points, list)
    assert all(isinstance(item, VariableList) for item in doe_points)


def test_generate_doe_lhs_level_count(cleanup_DOEVariable, cleanup, sample_variables):
    """Test DOEConfig generate_doe for LHS method missing level_count."""
    config = DOEConfig(
        sampling_method="LHS",
        variables=sample_variables,
        destination_folder=RESULTS_FOLDER_PATH,
        sampling_options={"level_count": 3, "use_level": 2},
    )

    doe_points = config.sampling_doe(sample_count=5)

    # Test that the return type is a list of VariableList instances
    assert isinstance(doe_points, list)
    assert all(isinstance(item, VariableList) for item in doe_points)


def test_write_doe_inputs_single_level(cleanup_DOEVariable, cleanup, sample_variables):
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
    _ = doe_config.sampling_doe(sample_count=5)

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


def test_write_doe_inputs_multilevel(cleanup_DOEVariable, cleanup, sample_variables):
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
    _ = doe_config.sampling_doe(sample_count=5)

    # Act
    doe_config._write_doe_inputs()

    # Assert
    output_file = destination_folder / f"DOE_inputs_3D_level{test_level}.csv"

    assert output_file.exists()

    written_data = pd.read_csv(output_file, sep=";", quotechar="|").drop("ID", axis=1)

    expected_data = doe_config.doe_points_df

    assert np.allclose(
        written_data.to_numpy(), expected_data.to_numpy(), atol=1e-4, rtol=1e-4
    )  # We are not checking using assert_frame_equal because the column name of the output file uses pseudo, while the VariableList returned by sampling_doe no
