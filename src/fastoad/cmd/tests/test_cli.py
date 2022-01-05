#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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

import os
import os.path as pth
from shutil import rmtree

import pandas as pd
import pytest
from click.testing import CliRunner

from fastoad.cmd.cli import fast_oad

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results", "cli")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    os.makedirs(RESULTS_FOLDER_PATH)  # needed for CliRunner.isolated_filesystem()


def test_plugin_info(cleanup, two_dummy_plugins, plugin_file_path):
    runner = CliRunner()
    result = runner.invoke(fast_oad, ["plugin_info"])

    assert not result.exception
    assert result.exit_code == 0

    expected_info = pd.DataFrame(
        dict(
            plugin_name=[f"test_plugin_{i}" for i in [1, 2, 3]],
            python_package=[f"dummy-{i}" for i in [1, 2, 3]],
            has_model_folder=[False, True, False],
            has_notebook_folder=[False, True, True],
            configurations=[
                ["dummy_conf_1.yml"],
                ["dummy_conf_2-1.yml", "dummy_conf_2-2.yaml"],
                [],
            ],
        )
    )
    assert result.output == expected_info.to_markdown(index=False) + "\n"
