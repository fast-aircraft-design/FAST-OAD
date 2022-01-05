"""
    Basic settings for tests
"""
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

# Note: this file has to be put in src/, not in project root folder, to ensure that
# `pytest src` will run OK after a `pip install .`

import os.path as pth

import pytest
from pkg_resources import Distribution, EntryPoint, get_distribution

from fastoad.module_management._plugins import FastoadLoader, MODEL_PLUGIN_ID

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "api", "results")
CONFIGURATION_FILE_PATH = pth.join(DATA_FOLDER_PATH, "sellar.yml")


@pytest.fixture
def plugin_file_path():
    """Returns the path to dummy plugins, for check purpose."""
    return pth.abspath("tests/dummy_plugins")


@pytest.fixture
def no_plugin():
    """
    Ensures that FAST-OAD has no plugin registered.

    Any previous state of plugins is restored during teardown.
    """
    original_entry_map = _update_entry_map({})
    yield
    _restore_entry_map(original_entry_map)


@pytest.fixture
def one_dummy_plugin():
    """
    Ensures that FAST-OAD has only the dummy plugin 1 registered.

    Any previous state of plugins is restored during teardown.
    """
    original_entry_map = _update_entry_map(
        {
            "test_plugin_1": EntryPoint(
                "test_plugin_1",
                "tests.dummy_plugins.dummy_plugin_1",
                dist=Distribution(project_name="dummy_1"),
            )
        }
    )
    yield
    _restore_entry_map(original_entry_map)


@pytest.fixture
def dummy_plugins():
    """
    Ensures that FAST-OAD has only the dummy plugins registered.

    Any previous state of plugins is restored during teardown.
    """
    original_entry_map = _update_entry_map(
        {
            f"test_plugin_{i}": EntryPoint(
                f"test_plugin_{i}",
                f"tests.dummy_plugins.dummy_plugin_{i}",
                dist=Distribution(project_name=f"dummy_{i}"),
            )
            for i in [1, 2, 3]
        }
    )
    yield
    _restore_entry_map(original_entry_map)


def _update_entry_map(new_entry_map) -> dict:
    dist = get_distribution("FAST-OAD")

    original_entry_map = dist.get_entry_map(MODEL_PLUGIN_ID).copy()
    entry_map = dist.get_entry_map(MODEL_PLUGIN_ID)
    entry_map.clear()
    entry_map.update(new_entry_map)

    # Ensure next instantiation of FastoadLoader will trigger reloading plugins
    FastoadLoader._loaded = False

    return original_entry_map


def _restore_entry_map(original_entry_map):
    dist = get_distribution("FAST-OAD")
    entry_map = dist.get_entry_map(MODEL_PLUGIN_ID)
    entry_map.clear()
    entry_map.update(original_entry_map)
    FastoadLoader._loaded = False
