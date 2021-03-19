#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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
import os.path as pth
from shutil import rmtree
from typing import IO, Union

import pytest

from .. import IVariableIOFormatter
from ..variable_io import DataFile
from ...openmdao.variables import Variable, VariableList

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


class DummyFormatter(IVariableIOFormatter):
    """
    Dummy formatter that contains data rather than reading/writing from/to a file.
    """

    def __init__(self, variables):
        self.variables = variables

    def read_variables(self, data_source: Union[str, IO]) -> VariableList:
        var_list = VariableList()
        var_list.update(self.variables, add_variables=True)
        return var_list

    def write_variables(self, data_source: Union[str, IO], variables: VariableList):
        self.variables.update(variables, add_variables=True)


def test(cleanup):
    file_path = pth.join(RESULTS_FOLDER_PATH, "dummy_data_file.xml")
    variables_1 = DataFile(file_path)
    assert len(variables_1) == 0

    variables_1.update(
        VariableList([Variable("data:foo", value=5), Variable("data:bar", value=10)]),
        add_variables=True,
    )
    variables_1.save()

    variables_2 = DataFile(file_path)
    assert len(variables_2) == 2

    assert set(variables_2) == set(variables_1)
