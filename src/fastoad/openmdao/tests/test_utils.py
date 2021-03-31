"""
Test module for OpenMDAO checks
"""
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

import openmdao.api as om

from .openmdao_sellar_example.disc1 import Disc1
from .openmdao_sellar_example.disc2 import Disc2
from .openmdao_sellar_example.functions import Functions
from .openmdao_sellar_example.sellar import Sellar
from .._utils import get_unconnected_input_names


def test_get_unconnected_input_names_single_component_group():
    # Test with a group problem with a single component (no promoted variable)
    group = om.Group()
    group.add_subsystem("disc1", Disc1())

    expected_mandatory_variables = {"disc1.x"}
    expected_optional_variables = {"disc1.y2", "disc1.z"}
    _test_problem(
        om.Problem(group), expected_mandatory_variables, expected_optional_variables, False
    )
    _test_problem(
        om.Problem(group), expected_mandatory_variables, expected_optional_variables, True
    )


def test_get_unconnected_input_names_one_component_and_ivc():
    group = om.Group()
    group.add_subsystem("disc1", Disc1())
    ivc = om.IndepVarComp()
    ivc.add_output("y2", 1.0)
    group.add_subsystem("inputs", ivc)
    group.connect("inputs.y2", "disc1.y2")

    expected_mandatory_variables = {"disc1.x"}
    expected_optional_variables = {"disc1.z"}
    _test_problem(
        om.Problem(group), expected_mandatory_variables, expected_optional_variables, False
    )
    _test_problem(
        om.Problem(group), expected_mandatory_variables, expected_optional_variables, True
    )


def test_get_unconnected_input_names_sellar_components():
    group = om.Group()
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])
    group.add_subsystem("functions", Functions(), promotes=["*"])

    expected_mandatory_variables = {"disc1.x", "functions.z"}
    expected_optional_variables = {"disc1.z", "disc2.z", "functions.x"}
    _test_problem(
        om.Problem(group), expected_mandatory_variables, expected_optional_variables, False
    )

    expected_mandatory_variables = {"z", "x"}
    expected_optional_variables = set()
    _test_problem(
        om.Problem(group), expected_mandatory_variables, expected_optional_variables, True
    )


def test_get_unconnected_input_names_full_sellar():
    expected_mandatory_variables = set()
    expected_optional_variables = set()
    _test_problem(
        om.Problem(Sellar()), expected_mandatory_variables, expected_optional_variables, False
    )
    _test_problem(
        om.Problem(Sellar()), expected_mandatory_variables, expected_optional_variables, True
    )


def _test_problem(
    problem,
    expected_missing_mandatory_variables,
    expected_missing_optional_variables,
    get_promoted_names,
):
    """ Tests get_unconnected_inputs for provided problem """

    problem.setup()

    mandatory, optional = get_unconnected_input_names(problem, promoted_names=get_promoted_names)
    assert set(mandatory) == expected_missing_mandatory_variables
    assert set(optional) == expected_missing_optional_variables
