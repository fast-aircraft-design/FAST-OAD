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

import openmdao.api as om
from numpy.testing import assert_allclose

from fastoad.io import VariableIO
from fastoad.models.performances.mission.openmdao.flight import SizingFlight
from tests.testing_utilities import run_system

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")


def test_sizing_flight():
    return
    # problem = FASTOADProblem()
    # problem.model = SizingFlight(propulsion_id="fastoad.wrapper.propulsion.rubber_engine")
    # problem.input_file_path = pth.join(DATA_FOLDER_PATH, "flight_inputs.xml")
    # problem.write_needed_inputs(
    #     r"D:\cdavid\PyCharmProjects\FAST-OAD\tests\integration_tests\oad_process\results\non_regression\problem_outputs.xml"
    # )

    input_file_path = pth.join(DATA_FOLDER_PATH, "flight_inputs.xml")
    ivc = VariableIO(input_file_path).read().to_ivc()

    problem = run_system(
        SizingFlight(propulsion_id="fastoad.wrapper.propulsion.rubber_engine"), ivc
    )

    assert_allclose(problem["data:mission:sizing:ZFW"], 65076.0, atol=1)
    # assert_allclose(problem["data:mission:sizing:fuel"], 8924.0, atol=1)

    om.convert_units()
