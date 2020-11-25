#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
from copy import deepcopy

import openmdao.api as om
import pytest

from ..aerodynamics import Aerodynamics
from ..defaults import set_all_input_defaults
from ..geometry import Geometry


def test_defaults():
    # Check with empty model (no incompatible variable definition)
    problem = om.Problem()
    set_all_input_defaults(problem.model)
    problem.setup()

    base_problem = om.Problem()
    base_problem.model.add_subsystem("geometry", Geometry(), promotes=["*"])
    base_problem.model.add_subsystem("aero", Aerodynamics(), promotes=["*"])

    # Check OpenMDAO error with incompatible variable definition
    problem = deepcopy(base_problem)
    with pytest.raises(RuntimeError):
        problem.setup()

    # Check that set_all_input_defaults fixes the error
    problem = deepcopy(base_problem)
    set_all_input_defaults(problem.model)
    problem.setup()

    # Check OpenMDAO fails correctly with additional incompatible variable definitions
    # (can happen with custom modules)
    problem = deepcopy(base_problem)

    class Comp1(om.ExplicitComponent):
        def setup(self):
            self.add_input("myvar", units="m")

    class Comp2(om.ExplicitComponent):
        def setup(self):
            self.add_input("myvar", units="km")

    problem.model.add_subsystem("comp1", Comp1(), promotes=["*"])
    problem.model.add_subsystem("comp2", Comp2(), promotes=["*"])

    set_all_input_defaults(problem.model)
    with pytest.raises(RuntimeError):
        problem.setup()
