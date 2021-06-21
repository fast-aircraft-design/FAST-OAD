#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

from .openmdao_sellar_example.sellar import Sellar
from ..problem import FASTOADProblem
from ..whatsopt import write_xdsm

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


# @pytest.mark.skip("This test requires access to the WhatsOpt server")
def test_write_xdsm(cleanup):

    problem = FASTOADProblem()
    problem.model.add_subsystem("sellar", Sellar(), promotes=["*"])
    problem.output_file_path = pth.join(RESULTS_FOLDER_PATH, "output.xml")
    problem.setup()
    problem.final_setup()

    xdsm_file_path = pth.join(RESULTS_FOLDER_PATH, "xdsm.html")
    write_xdsm(problem, xdsm_file_path)
    assert pth.exists(xdsm_file_path)
