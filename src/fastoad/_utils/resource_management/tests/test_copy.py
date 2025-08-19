# This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
# Copyright (c) 2025 ONERA & ISAE-SUPAERO
# FAST-OAD is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later

import shutil
from filecmp import dircmp
from pathlib import Path

import pytest

from . import resources
from ..copy import copy_resource_folder

RESOURCE_FOLDER_PATH = Path(__file__).parent / "resources"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results"


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_copy_resource_folder_from_str(cleanup):
    destination_folder = RESULTS_FOLDER_PATH / "test_from_str"
    copy_resource_folder("fastoad._utils.resource_management.tests.resources", destination_folder)
    _check_files(destination_folder)


def test_copy_resource_folder_from_str_with_exclusion(cleanup):
    destination_folder = RESULTS_FOLDER_PATH / "test_from_str_with_exclusion"
    excluded = ["__init__.py"]
    copy_resource_folder(
        "fastoad._utils.resource_management.tests.resources", destination_folder, exclude=excluded
    )
    _check_files(destination_folder, excluded)


def test_copy_resource_folder_from_package(cleanup):
    destination_folder = RESULTS_FOLDER_PATH / "test_from_module"
    copy_resource_folder(resources, destination_folder)
    _check_files(destination_folder)


def test_copy_resource_folder_from_package_with_exclusion(cleanup):
    destination_folder = RESULTS_FOLDER_PATH / "test_from_str_with_exclusion"
    excluded = ["__init__.py"]
    copy_resource_folder(resources, destination_folder, exclude=excluded)
    _check_files(destination_folder, excluded)


def _check_files(destination_folder, excluded=None):
    assert dircmp(RESOURCE_FOLDER_PATH, destination_folder, ignore=excluded)

    if excluded:
        for name in excluded:
            assert not next(destination_folder.rglob(name), False)
