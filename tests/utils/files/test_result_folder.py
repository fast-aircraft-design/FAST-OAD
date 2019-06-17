"""
Test module for subfolder_provider.py
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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
import shutil

from fastoad.module_management import BundleLoader
from fastoad.module_management.constants import SERVICE_RESULT_FOLDER_PROVIDER
from fastoad.utils.files.subfolder_provider import SubfolderProvider

FOLDER_NAME = 'my_result'
ROOT_FOLDER_PATH = pth.dirname(__file__)


def test_result_folder_provider():
    """ Tests SubfolderProvider"""
    provider: SubfolderProvider

    loader = BundleLoader()
    provider = loader.get_service(SERVICE_RESULT_FOLDER_PROVIDER)
    assert provider is not None

    expected_folder_path = pth.join(ROOT_FOLDER_PATH, FOLDER_NAME)

    # Check error if root folder is not set
    got_error = False
    try:
        _ = provider.get_subfolder_path(FOLDER_NAME)
    except AttributeError:
        got_error = True
    assert got_error

    # Check that folder is created
    if pth.exists(expected_folder_path):
        shutil.rmtree(expected_folder_path)
    provider.set_root_folder(ROOT_FOLDER_PATH)
    folder_path = provider.get_subfolder_path(FOLDER_NAME)
    assert pth.isdir(folder_path)

    # Check there is no problem if folder already exists
    same_folder_path = provider.get_subfolder_path([FOLDER_NAME])
    assert same_folder_path == folder_path

    # Check there is no problem if folder already exists
    subfolder_path = provider.get_subfolder_path([FOLDER_NAME, 'toto'])
    assert subfolder_path == pth.join(folder_path, 'toto')


def test_other_call_to_result_folder_provider():
    """ Checks that the root folder setting persists during run """
    provider: SubfolderProvider

    loader = BundleLoader()
    provider = loader.get_service(SERVICE_RESULT_FOLDER_PROVIDER)
    assert provider is not None
    assert provider.get_subfolder_path() == ROOT_FOLDER_PATH
