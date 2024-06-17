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

import pandas as pd
import pytest
from click.testing import CliRunner

from fastoad.cmd.cli import NOTEBOOK_FOLDER_NAME, fast_oad

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results"


@pytest.fixture(scope="session")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    RESULTS_FOLDER_PATH.mkdir(parents=True)


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
            source_data_files=[
                ["dummy_source_data_4-1.xml"],
                [
                    "dummy_source_data_3-1.xml",
                    "dummy_source_data_3-2.xml",
                    "dummy_source_data_3-3.xml",
                ],
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
        original_file = (
            plugin_root_path / "dist_1" / "dummy_plugin_1" / "configurations" / "dummy_conf_1-1.yml"
        )
        assert cmp(Path(temp_dir, "my_conf.yml"), original_file)
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")

        # Test overwrite prompt ================================================
        result = runner.invoke(fast_oad, ["gen_conf", "my_conf.yml"], input="n")
        assert not result.exception
        assert result.exit_code == 0
        assert "Do you want to overwrite it? [y/N]:" in result.output
        assert result.output.endswith("Operation cancelled.\n")

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

        # Test source data file specification =======================================
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
        original_file = (
            plugin_root_path / "dist_1" / "dummy_plugin_1" / "configurations" / "dummy_conf_1-1.yml"
        )
        assert cmp(Path(temp_dir, "my_conf.yml"), original_file)

        # ----------------------------------------------------------------------
        result = runner.invoke(
            fast_oad,
            ["gen_conf", "my_conf.yml", "-f", "-p", "dummy-dist-2", "-s", "dummy_conf_3-2.yaml"],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")
        original_file = (
            plugin_root_path
            / "dist_2"
            / "dummy_plugin_3"
            / "configurations"
            / "dummy_conf_3-2.yaml"
        )
        assert cmp(Path(temp_dir, "my_conf.yml"), original_file)


def test_gen_source_data_file_no_plugin(with_no_plugin):
    runner = CliRunner()
    result = runner.invoke(fast_oad, ["gen_source_data_file", "my_source.xml"])
    assert not result.exception
    assert result.exit_code == 0
    assert result.output == "This feature needs plugins, but no plugin available.\n"


def test_gen_source_data_file_one_plugin(cleanup, with_dummy_plugin_4, plugin_root_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH) as temp_dir:
        # Test minimal command =================================================
        result = runner.invoke(
            fast_oad,
            ["gen_source_data_file", "my_source.xml"],
        )
        original_file = (
            plugin_root_path
            / "dist_1"
            / "dummy_plugin_4"
            / "source_data_files"
            / "dummy_source_data_4-1.xml"
        )
        assert cmp(Path(temp_dir, "my_source.xml"), original_file)
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")

        # Test overwrite prompt ================================================
        result = runner.invoke(fast_oad, ["gen_source_data_file", "my_source.xml"], input="n")
        assert not result.exception
        assert result.exit_code == 0
        assert "Do you want to overwrite it? [y/N]:" in result.output
        assert result.output.endswith("Operation cancelled.\n")

        # ----------------------------------------------------------------------
        result = runner.invoke(fast_oad, ["gen_source_data_file", "my_source.xml"], input="y")
        assert not result.exception
        assert result.exit_code == 0
        assert "Do you want to overwrite it? [y/N]:" in result.output
        assert result.output.endswith("has been written.\n")

        # ----------------------------------------------------------------------
        result = runner.invoke(fast_oad, ["gen_source_data_file", "my_source.xml", "--force"])
        assert not result.exception
        assert result.exit_code == 0
        assert "Do you want to overwrite it? [y/N]:" not in result.output
        assert result.output.endswith("has been written.\n")

        # Test plugin specification ============================================
        result = runner.invoke(
            fast_oad,
            ["gen_source_data_file", "my_source.xml", "--from_package", "unknown-dist"],
            input="n",
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith(
            'No installed package with FAST-OAD plugin found with name "unknown-dist".\n'
        )

        # ----------------------------------------------------------------------
        result = runner.invoke(
            fast_oad, ["gen_source_data_file", "my_source.xml", "-f", "-p", "dummy-dist-1"]
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")

        # Test source file specification =======================================
        result = runner.invoke(
            fast_oad,
            [
                "gen_source_data_file",
                "my_source.xml",
                "-f",
                "-p",
                "dummy-dist-1",
                "-s",
                "dummy_source_data_4-1.xml",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")

        # ----------------------------------------------------------------------
        result = runner.invoke(
            fast_oad,
            [
                "gen_source_data_file",
                "my_source.xml",
                "-f",
                "--source",
                "dummy_source_data_4-1.xml",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")

        # ----------------------------------------------------------------------
        result = runner.invoke(
            fast_oad,
            [
                "gen_source_data_file",
                "my_source.xml",
                "-f",
                "--source",
                "unknown_source_data_file.xml",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith(
            '"unknown_source_data_file.xml" not provided with installed package "dummy-dist-1".\n'
        )


def test_gen_source_data_several_plugin(cleanup, with_dummy_plugins, plugin_root_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH) as temp_dir:
        # Test errors ==========================================================
        result = runner.invoke(
            fast_oad,
            ["gen_source_data_file", "my_source.xml"],
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
            ["gen_source_data_file", "my_source.xml", "-p", "dummy-dist-2"],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith(
            '"dummy-dist-2" provides several source data files. One must be specified.\n'
        )

        # ----------------------------------------------------------------------
        result = runner.invoke(
            fast_oad,
            [
                "gen_source_data_file",
                "my_source.xml",
                "-p",
                "dummy-dist-2",
                "-s",
                "unknown_source_data.xml",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith(
            '"unknown_source_data.xml" not provided with installed package "dummy-dist-2".\n'
        )

        # Test source file specification =======================================
        result = runner.invoke(
            fast_oad,
            [
                "gen_source_data_file",
                "my_source.xml",
                "-f",
                "-p",
                "dummy-dist-1",
                "-s",
                "dummy_source_data_4-1.xml",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")
        original_file = (
            plugin_root_path
            / "dist_1"
            / "dummy_plugin_4"
            / "source_data_files"
            / "dummy_source_data_4-1.xml"
        )
        assert cmp(Path(temp_dir, "my_source.xml"), original_file)

        # ----------------------------------------------------------------------
        result = runner.invoke(
            fast_oad,
            [
                "gen_source_data_file",
                "my_source.xml",
                "-f",
                "-p",
                "dummy-dist-2",
                "-s",
                "dummy_source_data_3-2.xml",
            ],
        )
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith("has been written.\n")
        original_file = (
            plugin_root_path
            / "dist_2"
            / "dummy_plugin_3"
            / "source_data_files"
            / "dummy_source_data_3-2.xml"
        )
        assert cmp(Path(temp_dir, "my_source.xml"), original_file)


def test_eval(cleanup):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH):
        result_1 = runner.invoke(
            fast_oad,
            [
                "gen_inputs",
                (DATA_FOLDER_PATH / "sellar.yml").as_posix(),
                (DATA_FOLDER_PATH / "inputs.xml").as_posix(),
                "--include_outputs",
            ],
        )
        assert not result_1.exception

        result_2 = runner.invoke(
            fast_oad,
            ["eval", (DATA_FOLDER_PATH / "sellar.yml").as_posix(), "-f"],
        )
        assert not result_2.exception


def test_optim(cleanup):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH):
        result_1 = runner.invoke(
            fast_oad,
            [
                "gen_inputs",
                (DATA_FOLDER_PATH / "sellar.yml").as_posix(),
                (DATA_FOLDER_PATH / "inputs.xml").as_posix(),
            ],
        )
        assert not result_1.exception

        result_2 = runner.invoke(
            fast_oad,
            ["optim", (DATA_FOLDER_PATH / "sellar.yml").as_posix(), "-f"],
        )
        assert not result_2.exception


def test_create_notebooks_with_no_notebook(cleanup, with_dummy_plugin_2, plugin_root_path):
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
        notebook_folder = Path(temp_dir, NOTEBOOK_FOLDER_NAME)

        # Test basic run =======================================================
        result = runner.invoke(fast_oad, ["notebooks"])
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.startswith(f'"{notebook_folder}" has been written')
        assert notebook_folder.exists()
        assert (notebook_folder / "test_plugin_1" / "notebook_1.ipynb").is_file()
        assert (notebook_folder / "test_plugin_4" / "notebook_1.ipynb").is_file()
        assert Path(temp_dir, NOTEBOOK_FOLDER_NAME, "test_plugin_4", "data").is_dir()

    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH) as temp_dir:
        notebook_folder = Path(temp_dir, NOTEBOOK_FOLDER_NAME)

        # Test basic run with package specification ============================
        result = runner.invoke(fast_oad, ["notebooks", "--from_package", "dummy-dist-1"])
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.startswith(f'"{notebook_folder}" has been written')
        assert notebook_folder.is_dir()
        assert (notebook_folder / "test_plugin_1" / "notebook_1.ipynb").is_file()
        assert (notebook_folder / "test_plugin_4" / "notebook_1.ipynb").is_file()
        assert Path(temp_dir, NOTEBOOK_FOLDER_NAME, "test_plugin_4", "data").is_dir()

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
        assert result.output.endswith("Operation cancelled.\n")

        # ----------------------------------------------------------------------
        result = runner.invoke(fast_oad, ["notebooks"], input="y")
        assert not result.exception
        assert result.exit_code == 0
        assert f'"{notebook_folder}" has been written' in result.output

        # Test path specification ==============================================
        result = runner.invoke(fast_oad, ["notebooks", "my_path"])
        assert not result.exception
        assert result.exit_code == 0
        assert (
            f'"{Path(temp_dir, "my_path", NOTEBOOK_FOLDER_NAME)}" has been written' in result.output
        )


def test_create_notebooks_with_plugins(cleanup, with_dummy_plugins, plugin_root_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH) as temp_dir:
        notebook_folder = Path(temp_dir, NOTEBOOK_FOLDER_NAME)

        # Test basic run =======================================================
        result = runner.invoke(fast_oad, ["notebooks"])
        assert not result.exception
        assert result.exit_code == 0
        assert notebook_folder.is_dir()
        assert (notebook_folder / "dummy-dist-1" / "test_plugin_1" / "notebook_1.ipynb").is_file()

        assert (notebook_folder / "dummy-dist-1" / "test_plugin_4" / "notebook_1.ipynb").is_file()
        assert Path(
            temp_dir, NOTEBOOK_FOLDER_NAME, "dummy-dist-1", "test_plugin_4", "data"
        ).is_dir()

        assert (notebook_folder / "dummy-dist-3").is_dir()
        assert (notebook_folder / "dummy-dist-3" / "notebook_2.ipynb").is_file()

    with runner.isolated_filesystem(temp_dir=RESULTS_FOLDER_PATH) as temp_dir:
        notebook_folder = Path(temp_dir, NOTEBOOK_FOLDER_NAME)

        # Test basic run with package specification ============================
        result = runner.invoke(fast_oad, ["notebooks", "-p", "dummy-dist-1"])
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.startswith(f'"{notebook_folder}" has been written')
        assert notebook_folder.is_dir()
        assert (notebook_folder / "test_plugin_1" / "notebook_1.ipynb").is_file()
        assert (notebook_folder / "test_plugin_4" / "notebook_1.ipynb").is_file()
        assert Path(temp_dir, NOTEBOOK_FOLDER_NAME, "test_plugin_4", "data").is_dir()

        # ----------------------------------------------------------------------
        result = runner.invoke(fast_oad, ["notebooks", "-p", "unknown-dist"])
        assert not result.exception
        assert result.exit_code == 0
        assert result.output.endswith(
            'No installed package with FAST-OAD plugin found with name "unknown-dist".\n'
        )
