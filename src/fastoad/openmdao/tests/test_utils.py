"""
Test module for OpenMDAO checks
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
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

import logging

import openmdao.api as om

from .sellar_example.disc1 import Disc1
from .sellar_example.disc2 import Disc2
from .sellar_example.functions import Functions
from .sellar_example.sellar import Sellar
from ..utils import get_unconnected_input_names

# Logger for this module
_LOGGER = logging.getLogger(__name__)


def test_get_unconnected_inputs():
    """ Tests get_unconnected_inputs() on a minimal problem  """
    # Check with Component as problem model -----------------------------------

    test_labels = []
    components = {}
    expected_mandatory_variables = {}
    expected_optional_variables = {}

    # Test with a group problem with a single component (no promoted variable)
    test_label = "single_component_group"
    test_labels.append(test_label)
    group = om.Group()
    group.add_subsystem("disc1", Disc1())
    components[test_label] = group
    expected_mandatory_variables[test_label] = ["disc1.x"]
    expected_optional_variables[test_label] = ["disc1.y2", "disc1.z"]

    # Test with a group problem with one component and some input
    test_label = "component+some_input"
    test_labels.append(test_label)
    group = om.Group()
    group.add_subsystem("disc1", Disc1())
    ivc = om.IndepVarComp()
    ivc.add_output("y2", 1.0)
    group.add_subsystem("inputs", ivc)
    group.connect("inputs.y2", "disc1.y2")
    components[test_label] = group
    expected_mandatory_variables[test_label] = ["disc1.x"]
    expected_optional_variables[test_label] = ["disc1.z"]

    # Test with a group problem with Sellar components
    test_label = "Sellar_components"
    test_labels.append(test_label)
    group = om.Group()
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])
    group.add_subsystem("functions", Functions(), promotes=["*"])
    components[test_label] = group
    expected_mandatory_variables[test_label] = ["disc1.x", "functions.z"]
    expected_optional_variables[test_label] = ["disc1.z", "disc2.z", "functions.x"]

    # Test with the fully set Sellar problem
    test_label = "Sellar"
    test_labels.append(test_label)
    components[test_label] = Sellar()
    expected_mandatory_variables[test_label] = []
    expected_optional_variables[test_label] = []

    for label in test_labels:
        _LOGGER.info("Testing %s -------------------" % label)
        problem = om.Problem(components[label])
        _test_problem(
            problem, expected_mandatory_variables[label], expected_optional_variables[label]
        )


def _test_problem(
    problem, expected_missing_mandatory_variables, expected_missing_optional_variables
):
    """ Tests get_unconnected_inputs for provided problem """

    # with logger provided
    mandatory, optional = get_unconnected_input_names(problem, logger=_LOGGER)
    assert sorted(mandatory) == sorted(expected_missing_mandatory_variables)
    assert sorted(optional) == sorted(expected_missing_optional_variables)

    # without providing logger
    mandatory, optional = get_unconnected_input_names(problem)
    assert sorted(mandatory) == sorted(expected_missing_mandatory_variables)
    assert sorted(optional) == sorted(expected_missing_optional_variables)
