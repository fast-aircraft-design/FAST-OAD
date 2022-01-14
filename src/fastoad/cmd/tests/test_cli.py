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
from filecmp import cmp
from shutil import rmtree

import pandas as pd
import pytest
from click.testing import CliRunner

from fastoad.cmd.cli import NOTEBOOK_FOLDER_NAME, fast_oad

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results", "cli")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    os.makedirs(RESULTS_FOLDER_PATH)  # needed for CliRunner.isolated_filesystem()


def test_plugin_info_no_plugin(with_no_plugin):
    runner = CliRunner()
    result = runner.invoke(fast_oad, ["plugin_info"])

    assert not result.exception
    assert result.exit_code == 0
    assert result.output == "No available FAST-OAD plugin.\n"


def test_plugin_info(with_dummy_plugins):
    runner = CliRunner()
    result = runner.invoke(fast_oad, ["plugin_info"])

    assert not result.exception
    assert result.exit_code == 0

    expected_info = pd.DataFrame(
        dict(
            installed_package=[f"dummy-dist-{i}" for i in [1, 2, 3]],
            has_models=[False, True, True],
            has_notebooks=[True, False, True],
            configurations=[
                ["dummy_conf_1-1.yml"],
                ["dummy_conf_2-1.yml", "dummy_conf_3-1.yml", "dummy_conf_3-2.yaml"],
                [],
            ],
        )
    )
    assert result.output == expected_info.to_markdown(index=False) + "\n"


def test_gen_conf_no_plugin(with_no_plugin):
    runner = CliRunner()
    result = runner.invoke(fast_oad, ["gen_conf", "my_conf.yml"])
    assert not result.exception
    assert result.exit_code == 0
    assert result.output == "This feature needs plugins, but no plugin available.\n"


def test_gen_conf_one_plugin(cleanup, with_dummy_plugin_1, plugin_root_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH) as temp_dir:
        # Test minimal command =================================================
        result = runner.invoke(
            fast_oad,
            ["gen_conf", "my_conf.yml"],
        )
        original_file = pth.join(
            plugin_root_path, "dist_1", "dummy_plugin_1", "configurations", "dummy_conf_1-1.yml"
        )
        assert cmp(pth.join(temp_dir, "my_conf.yml"), original_file)
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")

        # Test overwrite prompt ================================================
        result = runner.invoke(fast_oad, ["gen_conf", "my_conf.yml"], input="n")
        assert not result.exception
        assert result.exit_code == 0
        assert "Do you want to overwrite it? [y/N]:" in result.output
        assert result.output.endswith("No file written.\n")

        # ----------------------------------------------------------------------
        result = runner.invoke(fast_oad, ["gen_conf", "my_conf.yml"], input="y")
        assert not result.exception
        assert result.exit_code == 0
        assert "Do you want to overwrite it? [y/N]:" in result.output
        assert result.output.endswith("has been written.\n")

        # ----------------------------------------------------------------------
        result = runner.invoke(fast_oad, ["gen_conf", "my_conf.yml", "--force"])
        assert not result.exception
        assert result.exit_code == 0
        assert "Do you want to overwrite it? [y/N]:" not in result.output
        assert result.output.endswith("has been written.\n")

        # Test plugin specification ============================================
        result = runner.invoke(
            fast_oad, ["gen_conf", "my_conf.yml", "--from_package", "unknown-dist"], input="n"
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith(
            'No installed package with FAST-OAD plugin found with name "unknown-dist".\n'
        )

        # ----------------------------------------------------------------------
        result = runner.invoke(fast_oad, ["gen_conf", "my_conf.yml", "-f", "-p", "dummy-dist-1"])
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")

        # Test source file specification =======================================
        result = runner.invoke(
            fast_oad,
            ["gen_conf", "my_conf.yml", "-f", "-p", "dummy-dist-1", "-s", "dummy_conf_1-1.yml"],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")

        # ----------------------------------------------------------------------
        result = runner.invoke(
            fast_oad,
            ["gen_conf", "my_conf.yml", "-f", "--source", "dummy_conf_1-1.yml"],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")

        # ----------------------------------------------------------------------
        result = runner.invoke(
            fast_oad,
            ["gen_conf", "my_conf.yml", "-f", "--source", "unknown_conf.yml"],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith(
            '"unknown_conf.yml" not provided with installed package "dummy-dist-1".\n'
        )


def test_gen_conf_several_plugin(cleanup, with_dummy_plugins, plugin_root_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH) as temp_dir:
        # Test errors ==========================================================
        result = runner.invoke(
            fast_oad,
            ["gen_conf", "my_conf.yml"],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith(
            "Several installed packages with FAST-OAD plugins are available. "
            "One must be specified.\n"
        )

        # ----------------------------------------------------------------------
        result = runner.invoke(
            fast_oad,
            ["gen_conf", "my_conf.yml", "-p", "dummy-dist-2"],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith(
            '"dummy-dist-2" provides several configuration files. One must be specified.\n'
        )

        # ----------------------------------------------------------------------
        result = runner.invoke(
            fast_oad,
            ["gen_conf", "my_conf.yml", "-p", "dummy-dist-2", "-s", "unknown_conf.yml"],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith(
            '"unknown_conf.yml" not provided with installed package "dummy-dist-2".\n'
        )

        # Test source file specification =======================================
        result = runner.invoke(
            fast_oad,
            ["gen_conf", "my_conf.yml", "-f", "-p", "dummy-dist-1", "-s", "dummy_conf_1-1.yml"],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")
        original_file = pth.join(
            plugin_root_path, "dist_1", "dummy_plugin_1", "configurations", "dummy_conf_1-1.yml"
        )
        assert cmp(pth.join(temp_dir, "my_conf.yml"), original_file)

        # ----------------------------------------------------------------------
        result = runner.invoke(
            fast_oad,
            ["gen_conf", "my_conf.yml", "-f", "-p", "dummy-dist-2", "-s", "dummy_conf_3-2.yaml"],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")
        original_file = pth.join(
            plugin_root_path, "dist_2", "dummy_plugin_3", "configurations", "dummy_conf_3-2.yaml"
        )
        assert cmp(pth.join(temp_dir, "my_conf.yml"), original_file)


def test_create_notebooks_with_1_plugin(cleanup, with_dummy_plugin_1, plugin_root_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH):
        result = runner.invoke(fast_oad, ["notebooks"])
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("No notebook available in FAST-OAD plugins.\n")


def test_create_notebooks_with_1_distribution(
    cleanup, with_dummy_plugin_distribution_1, plugin_root_path
):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH) as temp_dir:
        # Test basic run =======================================================
        result = runner.invoke(fast_oad, ["notebooks"])
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.startswith("\nNotebooks have been created")
        assert pth.isdir(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME))
        assert pth.isfile(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME, "notebook_1.ipynb"))
        assert pth.isdir(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME, "data"))

    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH) as temp_dir:
        # Test basic run with package specification ============================
        result = runner.invoke(fast_oad, ["notebooks", "--from_package", "dummy-dist-1"])
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.startswith("\nNotebooks have been created")
        assert pth.isdir(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME))
        assert pth.isfile(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME, "notebook_1.ipynb"))
        assert pth.isdir(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME, "data"))

        # ----------------------------------------------------------------------
        result = runner.invoke(fast_oad, ["notebooks", "--from_package", "unknown-dist"])
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith(
            'No installed package with FAST-OAD plugin found with name "unknown-dist".\n'
        )

        # Test overwrite =======================================================
        result = runner.invoke(fast_oad, ["notebooks"], input="n")
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("cancelled.\n")

        # ----------------------------------------------------------------------
        result = runner.invoke(fast_oad, ["notebooks"], input="y")
        assert not result.exception
        assert result.exit_code == 0
        assert "Notebooks have been created" in result.output


def test_create_notebooks_with_plugins(cleanup, with_dummy_plugins, plugin_root_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH) as temp_dir:
        # Test basic run =======================================================
        result = runner.invoke(fast_oad, ["notebooks"])
        assert not result.exception
        assert result.exit_code == 0
        assert pth.isdir(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME))
        assert pth.isdir(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME, "dummy-dist-1"))
        assert pth.isfile(
            pth.join(temp_dir, NOTEBOOK_FOLDER_NAME, "dummy-dist-1", "notebook_1.ipynb")
        )
        assert pth.isdir(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME, "dummy-dist-1", "data"))

        assert pth.isdir(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME, "dummy-dist-3"))
        assert pth.isfile(
            pth.join(temp_dir, NOTEBOOK_FOLDER_NAME, "dummy-dist-3", "notebook_2.ipynb")
        )

    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH) as temp_dir:
        # Test basic run with package specification ============================
        result = runner.invoke(fast_oad, ["notebooks", "-p", "dummy-dist-1"])
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.startswith("\nNotebooks have been created")
        assert pth.isdir(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME))
        assert pth.isfile(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME, "notebook_1.ipynb"))
        assert pth.isdir(pth.join(temp_dir, NOTEBOOK_FOLDER_NAME, "data"))

        # ----------------------------------------------------------------------
        result = runner.invoke(fast_oad, ["notebooks", "-p", "unknown-dist"])
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith(
            'No installed package with FAST-OAD plugin found with name "unknown-dist".\n'
        )
