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

import logging
import shutil
from filecmp import cmp
from pathlib import Path
from unittest.mock import patch

import pytest

from fastoad.openmdao.variables import Variable, VariableList

from ..calc_runner import CalcRunner

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results" / Path(__file__).stem


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


# Mark this test as MPI-related
@pytest.mark.mpi
def test_one_run(cleanup):
    run_case = CalcRunner(configuration_file_path=DATA_FOLDER_PATH / "sellar2.yml")
    run_case.run(calculation_folder=RESULTS_FOLDER_PATH)


# Mark this test as MPI-related
@pytest.mark.mpi
def test_MPI_run_max_cpu(cleanup):
    run_case = CalcRunner(configuration_file_path=DATA_FOLDER_PATH / "sellar2.yml")

    input_vars = [
        VariableList([Variable("x", val=0.0), Variable("z", val=0.0)]),
        VariableList([Variable("x", val=10.0), Variable("z", val=0.0)]),
        VariableList([Variable("x", val=10.0), Variable("z", val=10.0)]),
        VariableList([Variable("x", val=0.0), Variable("z", val=10.0)]),
    ] * 3
    run_case.run_cases(
        input_vars,
        RESULTS_FOLDER_PATH / "with_MPI",
        use_MPI_if_available=True,
    )


# Mark this test as MPI-related
@pytest.mark.mpi
def test_MPI_run_2cpu(cleanup):
    run_case = CalcRunner(configuration_file_path=DATA_FOLDER_PATH / "sellar2.yml")

    input_vars = [
        VariableList([Variable("x", val=0.0), Variable("z", val=[0.0, 0.0], units="m**2")]),
        VariableList([Variable("x", val=10.0), Variable("z", val=[0.0, 0.0], units="m**2")]),
        VariableList([Variable("x", val=0.0), Variable("z", val=[10.0, 10.0], units="m**2")]),
        VariableList([Variable("x", val=10.0), Variable("z", val=[10.0, 10.0], units="m**2")]),
    ] * 3

    run_case.run_cases(
        input_vars,
        RESULTS_FOLDER_PATH / "with_MPI_2",
        max_workers=2,
        use_MPI_if_available=True,
    )

    # 2 calculations with an alternative input file. ---------------------------
    run_case = CalcRunner(
        configuration_file_path=DATA_FOLDER_PATH / "sellar2.yml",
        input_file_path=DATA_FOLDER_PATH / "inputs_alt.xml",
    )
    run_case.run_cases(
        [
            VariableList([Variable("x", val=0.0)]),
            VariableList([Variable("x", val=10.0)]),
        ],
        RESULTS_FOLDER_PATH / "with_MPI_2_alt",
        max_workers=2,
        use_MPI_if_available=True,
    )

    assert cmp(
        RESULTS_FOLDER_PATH / "with_MPI_2/calc_02" / "outputs.xml",
        RESULTS_FOLDER_PATH / "with_MPI_2_alt/calc_0" / "outputs.xml",
    )
    assert cmp(
        RESULTS_FOLDER_PATH / "with_MPI_2/calc_03" / "outputs.xml",
        RESULTS_FOLDER_PATH / "with_MPI_2_alt/calc_1" / "outputs.xml",
    )

    assert cmp(
        RESULTS_FOLDER_PATH / "with_MPI_2/calc_02" / "inputs.xml",
        RESULTS_FOLDER_PATH / "with_MPI_2_alt/calc_0" / "inputs_alt.xml",
    )
    assert cmp(
        RESULTS_FOLDER_PATH / "with_MPI_2/calc_03" / "inputs.xml",
        RESULTS_FOLDER_PATH / "with_MPI_2_alt/calc_1" / "inputs_alt.xml",
    )

    assert not cmp(  # And check all inputs are not the same
        RESULTS_FOLDER_PATH / "with_MPI_2/calc_03" / "inputs.xml",
        RESULTS_FOLDER_PATH / "with_MPI_2_alt/calc_0" / "inputs_alt.xml",
    )

    # Same with relative paths -------------------------------------------------
    run_case = CalcRunner(
        configuration_file_path=(DATA_FOLDER_PATH / "sellar2.yml").relative_to(Path.cwd()),
        input_file_path=(DATA_FOLDER_PATH / "inputs_alt.xml").relative_to(Path.cwd()),
    )
    run_case.run_cases(
        [
            VariableList([Variable("x", val=0.0)]),
            VariableList([Variable("x", val=10.0)]),
        ],
        RESULTS_FOLDER_PATH / "with_MPI_2_alt_relative",
        max_workers=2,
        use_MPI_if_available=True,
    )

    assert cmp(
        RESULTS_FOLDER_PATH / "with_MPI_2/calc_02" / "outputs.xml",
        RESULTS_FOLDER_PATH / "with_MPI_2_alt_relative/calc_0" / "outputs.xml",
    )
    assert cmp(
        RESULTS_FOLDER_PATH / "with_MPI_2/calc_03" / "outputs.xml",
        RESULTS_FOLDER_PATH / "with_MPI_2_alt_relative/calc_1" / "outputs.xml",
    )

    assert cmp(
        RESULTS_FOLDER_PATH / "with_MPI_2/calc_02" / "inputs.xml",
        RESULTS_FOLDER_PATH / "with_MPI_2_alt_relative/calc_0" / "inputs_alt.xml",
    )
    assert cmp(
        RESULTS_FOLDER_PATH / "with_MPI_2/calc_03" / "inputs.xml",
        RESULTS_FOLDER_PATH / "with_MPI_2_alt_relative/calc_1" / "inputs_alt.xml",
    )

    assert not cmp(  # And check all inputs are not the same
        RESULTS_FOLDER_PATH / "with_MPI_2/calc_03" / "inputs.xml",
        RESULTS_FOLDER_PATH / "with_MPI_2_alt_relative/calc_0" / "inputs_alt.xml",
    )


def test_multiprocessing_run_2cpu(cleanup):
    run_case = CalcRunner(configuration_file_path=DATA_FOLDER_PATH / "sellar2.yml")

    input_vars = [
        VariableList([Variable("x", val=0.0), Variable("z", val=0.0)]),
        VariableList([Variable("x", val=10.0), Variable("z", val=0.0)]),
        VariableList([Variable("x", val=10.0), Variable("z", val=10.0)]),
        VariableList([Variable("x", val=0.0), Variable("z", val=10.0)]),
    ] * 3

    run_case.run_cases(
        input_vars,
        RESULTS_FOLDER_PATH / "without_MPI_2",
        max_workers=2,
        use_MPI_if_available=False,
    )


def test_safe_run_catches_and_logs_fastoad_errors(caplog):
    """Test that _safe_run catches FAST-OAD errors and logs details for debugging.

    Without _safe_run, if one case fails due to any FAST-OAD error (convergence,
    invalid configuration, computation error, etc.), the entire batch crashes.
    _safe_run prevents this by catching exceptions, logging details, and returning None.
    """
    runner = CalcRunner(configuration_file_path=DATA_FOLDER_PATH / "sellar2.yml")
    input_values = VariableList([Variable("x", val=5.0), Variable("z", val=2.0)])
    calculation_folder = RESULTS_FOLDER_PATH / "test_safe_run_error"

    # Simulate FAST-OAD raising an error (could be any error: convergence, config, computation)
    error_message = "Convergence failed: model did not converge"
    with (
        patch.object(runner, "run", side_effect=RuntimeError(error_message)),
        caplog.at_level(logging.WARNING),
    ):
        result = CalcRunner._safe_run(runner, input_values, calculation_folder)

    # Verify None is returned instead of propagating the exception
    assert result is None
    # Verify error details are logged with context for debugging
    assert "Computation failed for folder" in caplog.text
    assert str(calculation_folder) in caplog.text
    assert error_message in caplog.text


def test_run_cases_continue_after_individual_failure(cleanup, caplog):
    """Test that run_cases completes even when individual cases fail due to FAST-OAD errors.

    This is the key benefit of _safe_run in batch operations: one failing case
    doesn't kill the entire batch. Failures are logged but the batch continues.

    This test uses actual FAST-OAD errors (not mocks) to demonstrate real robustness.
    """
    run_case = CalcRunner(configuration_file_path=DATA_FOLDER_PATH / "sellar2.yml")

    # Create input cases: valid, invalid (will fail in FAST-OAD), valid
    # The invalid case uses extreme values that cause convergence/computation errors
    input_vars = [
        VariableList([Variable("x", val=0.0), Variable("z", val=0.0)]),  # Case 0: OK
        VariableList(
            [Variable("x", val="not_a_number"), Variable("z", val=1e10)]
        ),  # Case 1: Will fail due to invalid input
        VariableList([Variable("x", val=10.0), Variable("z", val=10.0)]),  # Case 2: OK
    ]

    # Run with actual error occurring in case 1
    with caplog.at_level(logging.WARNING):
        results = run_case.run_cases(
            input_vars,
            RESULTS_FOLDER_PATH / "test_batch_continues",
            max_workers=1,
            use_MPI_if_available=False,
        )

    # All 3 cases should have results
    assert len(results) == 3
    # First and third succeed (DataFile objects), second fails (None)
    assert results[0] is not None, "First case should succeed"
    assert results[1] is None, "Second case should fail and return None due to extreme values"
    assert results[2] is not None, "Third case should succeed"
    # Verify the failure was logged (with all 3 cases completing)
    assert "Completed with 1 failures out of 3 cases" in caplog.text
