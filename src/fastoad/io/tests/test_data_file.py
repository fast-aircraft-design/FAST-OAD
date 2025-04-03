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

from __future__ import annotations

import shutil
from os import PathLike
from pathlib import Path
from typing import IO

import openmdao.api as om
import pytest

from .. import IVariableIOFormatter
from ..variable_io import DataFile
from ...openmdao.variables import Variable, VariableList

RESULTS_FOLDER_PATH = Path(__file__).parent / "results" / Path(__file__).stem


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


@pytest.fixture(scope="module")
def variables_ref():
    return VariableList([Variable("data:foo", value=5), Variable("data:bar", value=10)])


class DummyFormatter(IVariableIOFormatter):
    """
    Dummy formatter that contains data rather than reading/writing from/to a file.
    """

    def __init__(self, variables):
        self.variables = variables

    def read_variables(self, data_source: str | PathLike | IO) -> VariableList:
        var_list = VariableList()
        var_list.update(self.variables, add_variables=True)
        return var_list

    def write_variables(self, data_source: str | PathLike | IO, variables: VariableList):
        self.variables.update(variables, add_variables=True)


def test_datafile_save_read(cleanup, variables_ref):
    file_path = RESULTS_FOLDER_PATH / "dummy_data_file.xml"
    with pytest.raises(FileNotFoundError) as exc_info:
        _ = DataFile(file_path)
    assert exc_info.value.args[0] == f'File "{file_path}" is unavailable for reading.'

    data_file_1 = DataFile()
    assert len(data_file_1) == 0

    data_file_1.update(
        variables_ref,
        add_variables=True,
    )
    assert data_file_1.file_path is None
    with pytest.raises(FileNotFoundError):
        _ = data_file_1.save()
    data_file_1.save_as(file_path)
    assert data_file_1.file_path == file_path

    data_file_2 = DataFile(file_path)
    assert len(data_file_2) == 2

    assert set(data_file_2) == set(variables_ref)

    # Check using text file object --------------------
    with Path.open(file_path) as text_file_io:
        data_file_3 = DataFile(text_file_io)
    assert data_file_3 == data_file_2

    # Check using binary file object --------------------
    with Path.open(file_path, "rb") as binary_file_io:
        data_file_4 = DataFile(binary_file_io)
    assert data_file_4 == data_file_2


def test_datafile_from_ivc(variables_ref):
    ivc = variables_ref.to_ivc()
    data_file = DataFile.from_ivc(ivc)
    assert isinstance(data_file, DataFile)
    assert set(data_file) == set(variables_ref)


def test_datafile_from_dataframe(variables_ref):
    df = variables_ref.to_dataframe()
    data_file = DataFile.from_dataframe(df)
    assert isinstance(data_file, DataFile)
    assert set(data_file) == set(variables_ref)


def test_datafile_from_problem(variables_ref):
    pb = om.Problem()
    pb.model.add_subsystem("inputs", om.IndepVarComp("data:foo", val=5.0), promotes=["*"])
    pb.model.add_subsystem(
        "comp", om.ExecComp("b=2*a"), promotes=[("a", "data:foo"), ("b", "data:bar")]
    )
    pb.setup()
    pb.run_model()

    data_file = DataFile.from_problem(pb)

    assert isinstance(data_file, DataFile)
    assert set(data_file) == set(variables_ref)
