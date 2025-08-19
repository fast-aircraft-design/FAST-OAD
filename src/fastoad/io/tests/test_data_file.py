import shutil
from os import PathLike
from pathlib import Path
from typing import IO, Union

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

    def read_variables(self, data_source: Union[str, PathLike, IO]) -> VariableList:
        var_list = VariableList()
        var_list.update(self.variables, add_variables=True)
        return var_list

    def write_variables(self, data_source: Union[str, PathLike, IO], variables: VariableList):
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
    with open(file_path) as text_file_io:
        data_file_3 = DataFile(text_file_io)
    assert data_file_3 == data_file_2

    # Check using binary file object --------------------
    with open(file_path, "rb") as binary_file_io:
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
    pb = om.Problem(reports=False)
    pb.model.add_subsystem("inputs", om.IndepVarComp("data:foo", val=5.0), promotes=["*"])
    pb.model.add_subsystem(
        "comp", om.ExecComp("b=2*a"), promotes=[("a", "data:foo"), ("b", "data:bar")]
    )
    pb.setup()
    pb.run_model()

    data_file = DataFile.from_problem(pb)

    assert isinstance(data_file, DataFile)
    assert set(data_file) == set(variables_ref)
