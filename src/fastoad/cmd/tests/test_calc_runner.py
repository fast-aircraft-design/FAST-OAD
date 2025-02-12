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
from filecmp import cmp
from pathlib import Path

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
