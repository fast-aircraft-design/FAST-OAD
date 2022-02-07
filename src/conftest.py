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
import sys
from typing import List
from unittest.mock import Mock

import pytest

if sys.version_info < (3, 10):
    from importlib_metadata import EntryPoint, distribution, Distribution, EntryPoints
else:
    from importlib.metadata import EntryPoint, distribution, Distribution, EntryPoints

from fastoad.module_management._plugins import FastoadLoader, MODEL_PLUGIN_ID

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "api", "results")
CONFIGURATION_FILE_PATH = pth.join(DATA_FOLDER_PATH, "sellar.yml")


@pytest.fixture
def plugin_root_path() -> str:
    """Returns the path to dummy plugins, for check purpose."""
    return pth.abspath("tests/dummy_plugins")


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
    (one configuration file, no models, notebook folder).

    Any previous state of plugins is restored during teardown.
    """
    _setup()
    dummy_dist_1 = Mock(Distribution)
    dummy_dist_1.name = "dummy-dist-1"
    entry_points = [
        EntryPoint(
            name="test_plugin_1",
            value="tests.dummy_plugins.dist_1.dummy_plugin_1",
            group=MODEL_PLUGIN_ID,
        )
    ]
    entry_points[0].dist = dummy_dist_1
    _update_entry_map(entry_points)
    yield
    _teardown()


@pytest.fixture
def with_dummy_plugin_2():
    """
    Reduces plugin list to dummy-dist-2 with plugin test_plugin_2
    (one configuration file, model folder, no notebooks).

    Any previous state of plugins is restored during teardown.
    """
    _setup()
    dummy_dist_2 = Mock(Distribution)
    dummy_dist_2.name = "dummy-dist-2"
    entry_points = [
        EntryPoint(
            name="test_plugin_2",
            value="tests.dummy_plugins.dist_2.dummy_plugin_2",
            group=MODEL_PLUGIN_ID,
        )
    ]
    entry_points[0].dist = dummy_dist_2
    _update_entry_map(entry_points)
    yield
    _teardown()


@pytest.fixture
def with_dummy_plugin_4():
    """
    Reduces plugin list to dummy-dist-1 with plugin test_plugin_4
    (no configuration file, no model folder, notebooks).

    Any previous state of plugins is restored during teardown.
    """
    _setup()
    dummy_dist_1 = Mock(Distribution)
    dummy_dist_1.name = "dummy-dist-1"
    entry_points = [
        EntryPoint(
            name="test_plugin_4",
            value="tests.dummy_plugins.dist_1.dummy_plugin_4",
            group=MODEL_PLUGIN_ID,
        )
    ]
    entry_points[0].dist = dummy_dist_1
    _update_entry_map(entry_points)
    yield
    _teardown()


@pytest.fixture
def with_dummy_plugin_distribution_1():
    """
    Reduces plugin list to dummy-dist-1 with plugins test_plugin_1 and test_plugin_4
    (one configuration file, no models, notebook folder).

    Any previous state of plugins is restored during teardown.
    """
    _setup()
    dummy_dist_1 = Mock(Distribution)
    dummy_dist_1.name = "dummy-dist-1"
    entry_points = [
        EntryPoint(
            name="test_plugin_1",
            value="tests.dummy_plugins.dist_1.dummy_plugin_1",
            group=MODEL_PLUGIN_ID,
        ),
        EntryPoint(
            name="test_plugin_4",
            value="tests.dummy_plugins.dist_1.dummy_plugin_4",
            group=MODEL_PLUGIN_ID,
        ),
    ]

    entry_points[0].dist = entry_points[1].dist = dummy_dist_1

    _update_entry_map(entry_points)
    yield
    _teardown()


@pytest.fixture
def with_dummy_plugins():
    """
    Reduces plugin list to:
        - dummy-dist-1 with plugins test_plugin_1 and test_plugin_4
          (one configuration file, no models, notebook folder).
        - dummy-dist-2 with plugins test_plugin_2 and test_plugin_3
          (3 configuration files, model folder, no notebooks).
        - dummy-dist-3 with plugins test_plugin_5
          (no configuration file, model folder, notebook folder).

    Any previous state of plugins is restored during teardown.
    """
    _setup()
    dummy_dist_1 = Mock(Distribution)
    dummy_dist_1.name = "dummy-dist-1"
    dummy_dist_2 = Mock(Distribution)
    dummy_dist_2.name = "dummy-dist-2"
    dummy_dist_3 = Mock(Distribution)
    dummy_dist_3.name = "dummy-dist-3"
    entry_points = [
        EntryPoint(
            name="test_plugin_1",
            value="tests.dummy_plugins.dist_1.dummy_plugin_1",
            group=MODEL_PLUGIN_ID,
        ),
        EntryPoint(
            name="test_plugin_4",
            value="tests.dummy_plugins.dist_1.dummy_plugin_4",
            group=MODEL_PLUGIN_ID,
        ),
        EntryPoint(
            name="test_plugin_2",
            value="tests.dummy_plugins.dist_2.dummy_plugin_2",
            group=MODEL_PLUGIN_ID,
        ),
        EntryPoint(
            name="test_plugin_3",
            value="tests.dummy_plugins.dist_2.dummy_plugin_3",
            group=MODEL_PLUGIN_ID,
        ),
        EntryPoint(
            name="test_plugin_5",
            value="tests.dummy_plugins.dist_3.dummy_plugin_5",
            group=MODEL_PLUGIN_ID,
        ),
    ]
    entry_points[0].dist = entry_points[1].dist = dummy_dist_1
    entry_points[2].dist = entry_points[3].dist = dummy_dist_2
    entry_points[4].dist = dummy_dist_3

    _update_entry_map(entry_points)
    yield
    _teardown()


ORIGINAL_ENTRY_POINTS_PROPERTY = Distribution.entry_points
try:
    ORIGINAL_ENTRY_POINT_SETATTR = Distribution.__setattr__
except AttributeError:
    ORIGINAL_ENTRY_POINT_SETATTR = None


def _update_entry_map(new_plugin_entry_points: List[EntryPoint]):
    """
    Modified plugin entry_points of FAST-OAD distribution.

    This is done by replacing the entry_points property of Distribution class

    :param new_plugin_entry_points:
    """
    dist: Distribution = distribution("FAST-OAD")

    entry_points = EntryPoints(
        [ep for ep in dist.entry_points if ep.group != MODEL_PLUGIN_ID] + new_plugin_entry_points
    )

    # Distribution.entry_points gets info directly from entry_points.txt.
    # Therefore, the only way to modify the output of Distribution.entry_points
    # is to replace the property.
    setattr(Distribution, "entry_points", property(lambda self: entry_points))

    # Ensure next instantiation of FastoadLoader will trigger reloading plugins
    FastoadLoader._loaded = False


def _setup():
    # In last versions of importlib-metadata, EntryPoint overloads __setattr__ to
    # prevent any attribute modification, but it does not suit our needs.
    try:
        delattr(EntryPoint, "__setattr__")
    except AttributeError:
        pass


def _teardown():
    if ORIGINAL_ENTRY_POINT_SETATTR:
        setattr(EntryPoint, "__setattr__", ORIGINAL_ENTRY_POINT_SETATTR)
    setattr(Distribution, "entry_points", ORIGINAL_ENTRY_POINTS_PROPERTY)
    FastoadLoader._loaded = False
