"""
Basic settings for tests
"""
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

# Note: this file has to be put in src/, not in project root folder, to ensure that
# `pytest src` will run OK after a `pip install .`

import sys
from pathlib import Path
from platform import system
from shutil import which
from typing import List, Optional
from unittest.mock import Mock

import pytest
import wrapt

if sys.version_info >= (3, 10):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata

from fastoad.module_management._plugins import MODEL_PLUGIN_ID, FastoadLoader


@pytest.fixture(autouse=True)
def no_xfoil_skip(request, xfoil_path):
    """
    Use @pytest.mark.skip_if_no_xfoil() before a test to skip it if xfoil_path
    fixture returns None and OS is not Windows.
    """
    if request.node.get_closest_marker("skip_if_no_xfoil"):
        if xfoil_path is None and system() != "Windows":
            pytest.skip("No XFOIL executable available")


@pytest.fixture
def xfoil_path() -> Optional[str]:
    """
    On a system that is not Windows, a XFOIL executable with name "xfoil" can
    be put in "<project_root>/tests/xfoil_exe/".
    In this case, this fixture will return its path.

    :return: The path of the XFOIL executable
    """
    if system() == "Windows":
        # On Windows, we use the embedded executable
        return None

    path = Path("tests/xfoil_exe", "xfoil").resolve()
    if path.exists():
        # If there is a local xfoil, use it
        return path.as_posix()

    # Otherwise, use one that is in PATH, if it exists
    return which("xfoil")


@pytest.fixture
def plugin_root_path() -> Path:
    """Returns the path to dummy plugins, for check purpose."""
    return (Path(__file__).parent.parent / "tests" / "dummy_plugins").resolve()


@pytest.fixture
def with_no_plugin():
    """
    Ensures that FAST-OAD has no plugin registered.

    Any previous state of plugins is restored during teardown.
    """
    _update_entry_map([])
    yield
    _teardown()


@pytest.fixture
def with_dummy_plugin_1():
    """
    Reduces plugin list to dummy-dist-1 with plugin test_plugin_1
    (one configuration file, no models, notebook folder, no source data files).

    Any previous state of plugins is restored during teardown.
    """
    _setup()
    dummy_dist_1 = Mock(importlib_metadata.Distribution)
    dummy_dist_1.name = "dummy-dist-1"
    new_entry_points = [
        importlib_metadata.EntryPoint(
            name="test_plugin_1",
            value="tests.dummy_plugins.dist_1.dummy_plugin_1",
            group=MODEL_PLUGIN_ID,
        )
    ]
    new_entry_points[0].dist = dummy_dist_1
    _update_entry_map(new_entry_points)
    yield
    _teardown()


@pytest.fixture
def with_dummy_plugin_2():
    """
    Reduces plugin list to dummy-dist-2 with plugin test_plugin_2
    (one configuration file, model folder, no notebooks, no source data files).

    Any previous state of plugins is restored during teardown.
    """
    _setup()
    dummy_dist_2 = Mock(importlib_metadata.Distribution)
    dummy_dist_2.name = "dummy-dist-2"
    new_entry_points = [
        importlib_metadata.EntryPoint(
            name="test_plugin_2",
            value="tests.dummy_plugins.dist_2.dummy_plugin_2",
            group=MODEL_PLUGIN_ID,
        )
    ]
    new_entry_points[0].dist = dummy_dist_2
    _update_entry_map(new_entry_points)
    yield
    _teardown()


@pytest.fixture
def with_dummy_plugin_4():
    """
    Reduces plugin list to dummy-dist-1 with plugin test_plugin_4
    (no configuration file, no model folder, notebooks, one source data file).

    Any previous state of plugins is restored during teardown.
    """
    _setup()
    dummy_dist_1 = Mock(importlib_metadata.Distribution)
    dummy_dist_1.name = "dummy-dist-1"
    new_entry_points = [
        importlib_metadata.EntryPoint(
            name="test_plugin_4",
            value="tests.dummy_plugins.dist_1.dummy_plugin_4",
            group=MODEL_PLUGIN_ID,
        )
    ]
    new_entry_points[0].dist = dummy_dist_1
    _update_entry_map(new_entry_points)
    yield
    _teardown()


@pytest.fixture
def with_dummy_plugin_distribution_1():
    """
    Reduces plugin list to dummy-dist-1 with plugins test_plugin_1 and test_plugin_4
    (one configuration file, no models, notebook folder, one source data file).

    Any previous state of plugins is restored during teardown.
    """
    _setup()
    dummy_dist_1 = Mock(importlib_metadata.Distribution)
    dummy_dist_1.name = "dummy-dist-1"
    new_entry_points = [
        importlib_metadata.EntryPoint(
            name="test_plugin_1",
            value="tests.dummy_plugins.dist_1.dummy_plugin_1",
            group=MODEL_PLUGIN_ID,
        ),
        importlib_metadata.EntryPoint(
            name="test_plugin_4",
            value="tests.dummy_plugins.dist_1.dummy_plugin_4",
            group=MODEL_PLUGIN_ID,
        ),
    ]

    new_entry_points[0].dist = new_entry_points[1].dist = dummy_dist_1

    _update_entry_map(new_entry_points)
    yield
    _teardown()


@pytest.fixture
def with_dummy_plugin_distribution_1_and_3():
    """
    Reduces plugin list to dummy-dist-1 and dummy-dist-3
    (one configuration file (in dist 1), models, notebook folder, one source data file (in dist 1)).

    Any previous state of plugins is restored during teardown.
    """
    _setup()
    dummy_dist_1 = Mock(importlib_metadata.Distribution)
    dummy_dist_1.name = "dummy-dist-1"
    dummy_dist_3 = Mock(importlib_metadata.Distribution)
    dummy_dist_3.name = "dummy-dist-3"
    new_entry_points = [
        importlib_metadata.EntryPoint(
            name="test_plugin_1",
            value="tests.dummy_plugins.dist_1.dummy_plugin_1",
            group=MODEL_PLUGIN_ID,
        ),
        importlib_metadata.EntryPoint(
            name="test_plugin_4",
            value="tests.dummy_plugins.dist_1.dummy_plugin_4",
            group=MODEL_PLUGIN_ID,
        ),
        importlib_metadata.EntryPoint(
            name="test_plugin_5",
            value="tests.dummy_plugins.dist_3.dummy_plugin_5",
            group=MODEL_PLUGIN_ID,
        ),
    ]
    new_entry_points[0].dist = new_entry_points[1].dist = dummy_dist_1
    new_entry_points[2].dist = dummy_dist_3

    _update_entry_map(new_entry_points)
    yield
    _teardown()


@pytest.fixture
def with_dummy_plugins():
    """
    Reduces plugin list to:
        - dummy-dist-1 with plugins test_plugin_1 and test_plugin_4
          (one configuration file, no models, notebook folder, one source data file).
        - dummy-dist-2 with plugins test_plugin_2 and test_plugin_3
          (3 configuration files, model folder, no notebooks, 3 source data files).
        - dummy-dist-3 with plugins test_plugin_5
          (no configuration file, model folder, notebook folder, no source data files).

    Any previous state of plugins is restored during teardown.
    """
    _setup()
    dummy_dist_1 = Mock(importlib_metadata.Distribution)
    # Here we intentionally use an unconventional name (upper case, with underscore)
    dummy_dist_1.name = "DUMMY_DIST-1"
    dummy_dist_2 = Mock(importlib_metadata.Distribution)
    dummy_dist_2.name = "dummy-dist-2"
    dummy_dist_3 = Mock(importlib_metadata.Distribution)
    dummy_dist_3.name = "dummy-dist-3"
    new_entry_points = [
        importlib_metadata.EntryPoint(
            name="test_plugin_1",
            value="tests.dummy_plugins.dist_1.dummy_plugin_1",
            group=MODEL_PLUGIN_ID,
        ),
        importlib_metadata.EntryPoint(
            name="test_plugin_4",
            value="tests.dummy_plugins.dist_1.dummy_plugin_4",
            group=MODEL_PLUGIN_ID,
        ),
        importlib_metadata.EntryPoint(
            name="test_plugin_2",
            value="tests.dummy_plugins.dist_2.dummy_plugin_2",
            group=MODEL_PLUGIN_ID,
        ),
        importlib_metadata.EntryPoint(
            name="test_plugin_3",
            value="tests.dummy_plugins.dist_2.dummy_plugin_3",
            group=MODEL_PLUGIN_ID,
        ),
        importlib_metadata.EntryPoint(
            name="test_plugin_5",
            value="tests.dummy_plugins.dist_3.dummy_plugin_5",
            group=MODEL_PLUGIN_ID,
        ),
    ]
    new_entry_points[0].dist = new_entry_points[1].dist = dummy_dist_1
    new_entry_points[2].dist = new_entry_points[3].dist = dummy_dist_2
    new_entry_points[4].dist = dummy_dist_3

    _update_entry_map(new_entry_points)
    yield
    _teardown()


def _update_entry_map(new_plugin_entry_points: List[importlib_metadata.EntryPoint]):
    """
    Modified plugin entry_points of FAST-OAD distribution.

    This is done by replacing the entry_points property of Distribution class

    :param new_plugin_entry_points:
    """
    BypassEntryPointReading.entry_points = new_plugin_entry_points
    BypassEntryPointReading.active = True
    FastoadLoader._loaded = False


def _setup():
    MakeEntryPointMutable.active = True


def _teardown():
    MakeEntryPointMutable.active = False
    BypassEntryPointReading.active = False
    FastoadLoader._loaded = False


# Monkey-patching using wrapt module ###########################################


def _BypassEntryPointReading_enabled():
    return BypassEntryPointReading.active


class BypassEntryPointReading:
    active = False
    entry_points = []

    @wrapt.decorator(enabled=_BypassEntryPointReading_enabled)
    def __call__(self, wrapped, instance, args, kwargs):
        if kwargs.get("group") == MODEL_PLUGIN_ID:
            return self.entry_points
        else:
            return wrapped(*args, **kwargs)


importlib_metadata.entry_points = BypassEntryPointReading()(importlib_metadata.entry_points)


def _MakeEntryPointMutable_enabled():
    return MakeEntryPointMutable.active


class MakeEntryPointMutable:
    active = True

    @classmethod
    def _enabled(cls):
        return cls.active

    @wrapt.decorator(enabled=_MakeEntryPointMutable_enabled)
    def __call__(self, wrapped, instance, args, kwargs):
        try:
            delattr(wrapped, "__setattr__")
        except AttributeError:
            pass
        return wrapped(*args, **kwargs)


importlib_metadata.EntryPoint = MakeEntryPointMutable()(importlib_metadata.EntryPoint)
