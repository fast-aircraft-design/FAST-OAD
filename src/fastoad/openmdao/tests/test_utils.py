"""
Test module for OpenMDAO checks
"""

import openmdao.api as om
import pytest

from .openmdao_sellar_example.disc1 import Disc1
from .openmdao_sellar_example.disc2 import Disc2
from .openmdao_sellar_example.functions import FunctionF, FunctionG1, FunctionG2
from .openmdao_sellar_example.sellar import SellarModel
from .._utils import get_unconnected_input_names

pytestmark = pytest.mark.filterwarnings(
    "ignore:Call to deprecated function \(or staticmethod\) get_unconnected_input_names"
)


def test_get_unconnected_input_names_single_component_group():
    # Test with a group problem with a single component (no promoted variable)
    group = om.Group()
    group.add_subsystem("disc1", Disc1())

    expected_mandatory_variables = {"disc1.x"}
    expected_optional_variables = {"disc1.y2", "disc1.z"}
    _test_problem(
        om.Problem(group, reports=False),
        expected_mandatory_variables,
        expected_optional_variables,
        False,
    )
    _test_problem(
        om.Problem(group, reports=False),
        expected_mandatory_variables,
        expected_optional_variables,
        True,
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
        om.Problem(group, reports=False),
        expected_mandatory_variables,
        expected_optional_variables,
        False,
    )
    _test_problem(
        om.Problem(group, reports=False),
        expected_mandatory_variables,
        expected_optional_variables,
        True,
    )


def test_get_unconnected_input_names_sellar_components():
    group = om.Group()
    group.add_subsystem("disc1", Disc1(), promotes=["*"])
    group.add_subsystem("disc2", Disc2(), promotes=["*"])
    group.add_subsystem("functions", FunctionF(), promotes=["*"])
    group.add_subsystem("constaint1", FunctionG1(), promotes=["*"])
    group.add_subsystem("constaint2", FunctionG2(), promotes=["*"])

    expected_mandatory_variables = {"disc1.x", "functions.z"}
    expected_optional_variables = {"disc1.z", "disc2.z", "functions.x"}
    _test_problem(
        om.Problem(group, reports=False),
        expected_mandatory_variables,
        expected_optional_variables,
        False,
    )

    expected_mandatory_variables = {"z", "x"}
    expected_optional_variables = set()
    _test_problem(
        om.Problem(group, reports=False),
        expected_mandatory_variables,
        expected_optional_variables,
        True,
    )


def test_get_unconnected_input_names_full_sellar():
    expected_mandatory_variables = {"objective.z"}
    expected_optional_variables = {"disc1.z", "disc2.z"}
    _test_problem(
        om.Problem(SellarModel(), reports=False),
        expected_mandatory_variables,
        expected_optional_variables,
        False,
    )
    expected_mandatory_variables = {"z"}
    expected_optional_variables = set()
    _test_problem(
        om.Problem(SellarModel(), reports=False),
        expected_mandatory_variables,
        expected_optional_variables,
        True,
    )


def _test_problem(
    problem,
    expected_missing_mandatory_variables,
    expected_missing_optional_variables,
    get_promoted_names,
):
    """Tests get_unconnected_inputs for provided problem"""

    problem.setup()
    problem.final_setup()

    mandatory, optional = get_unconnected_input_names(problem, promoted_names=get_promoted_names)
    assert set(mandatory) == expected_missing_mandatory_variables
    assert set(optional) == expected_missing_optional_variables
