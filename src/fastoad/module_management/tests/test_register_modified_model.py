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

import os.path as pth
from pathlib import Path

import pytest

from .._plugins import FastoadLoader
from ..exceptions import FastTooManySubmodelsError
from ..service_registry import RegisterOpenMDAOSystem
from ..._utils.testing import run_system

DATA_FOLDER_PATH = Path(__file__).parent.joinpath("data")


@pytest.fixture(scope="module")
def load():
    """Loads components"""
    FastoadLoader()
    RegisterOpenMDAOSystem.explore_folder(
        pth.join(DATA_FOLDER_PATH, "sellar_example_with_submodels")
    )
    a = 1


def test_register_modified_model(load):

    standard_sellar = RegisterOpenMDAOSystem.get_system("test_assembly.sellar.standard")
    sellar1 = RegisterOpenMDAOSystem.get_system("test_assembly.sellar.alternate_1")
    sellar2 = RegisterOpenMDAOSystem.get_system("test_assembly.sellar.alternate_2")
    sellar3 = RegisterOpenMDAOSystem.get_system("test_assembly.sellar.alternate_3")

    with pytest.raises(FastTooManySubmodelsError):
        standard_problem = run_system(standard_sellar)
    problem1 = run_system(sellar1)
    problem2 = run_system(sellar1)
    problem3 = run_system(sellar1)
