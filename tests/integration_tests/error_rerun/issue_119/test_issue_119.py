"""
Test module for Overall Aircraft Design process
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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

import pytest

import fastoad
from fastoad import api

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), 'data')
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), 'results')


@pytest.fixture(scope='module')
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


@pytest.fixture(scope='module')
def install_components():
    """ Needed because other tests play with Pelix/iPOPO """
    fastoad.initialize_framework.load()


def test_issue_119(cleanup, install_components):
    configuration_file_path = pth.join(DATA_FOLDER_PATH, 'oad_process.toml')

    # Run model ---------------------------------------------------------------
    problem = api.evaluate_problem(configuration_file_path, True)
