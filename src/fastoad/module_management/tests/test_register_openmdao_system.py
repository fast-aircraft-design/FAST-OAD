"""
Test module for openmdao_system_registry.py
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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
from pathlib import Path

import openmdao.api as om
import pytest

from .data.module_sellar_example.disc2.disc2 import RegisteredDisc2
from .._bundle_loader import BundleLoader
from ..constants import ModelDomain, SERVICE_OPENMDAO_SYSTEM
from ..exceptions import FastBadSystemOptionError, FastBundleLoaderUnknownFactoryNameError
from ..service_registry import RegisterOpenMDAOSystem
from ..._utils.sellar.sellar_base import BasicSellarModel, BasicSellarProblem, ISellarFactory
from ...openmdao.variables import Variable

_LOGGER = logging.getLogger(__name__)  # Logger for this module


DATA_FOLDER_PATH = Path(__file__).parent / "data"


@pytest.fixture(scope="module")
def load():
    """Loads components"""
    RegisterOpenMDAOSystem.explore_folder(DATA_FOLDER_PATH / "module_sellar_example")


def test_variable_description(load):
    """
    The variable description file must have been read during explore_folder()
    """
    assert Variable("x").description == ""  # No description provided
    assert Variable("z").description == 'the "Z" variable :)'  # this description is at folder root
    assert (
        Variable("y1").description == 'the "Y1" variable !'
    )  # this description is in a subpackage


def test_components_alone(load):
    """
    Simple test of existence of "openmdao.component" service factories
    """

    services = BundleLoader().get_factory_names(SERVICE_OPENMDAO_SYSTEM)
    assert services


def test_get_system(load):
    """
    Tests the retrieval of a System according to identifier
    """

    # Get component 1 #########################################################
    # Tests also the definition of model domain
    disc1_component = RegisterOpenMDAOSystem.get_system("module_management_test.sellar.disc1")
    assert (
        RegisterOpenMDAOSystem.get_provider_domain("module_management_test.sellar.disc1").value
        == ModelDomain.OTHER.value
    )
    assert (
        RegisterOpenMDAOSystem.get_provider_domain(disc1_component).value == ModelDomain.OTHER.value
    )
    assert RegisterOpenMDAOSystem.get_provider_description(disc1_component) == "some text"
    assert disc1_component is not None
    disc1_component.setup()
    outputs = {}
    disc1_component.compute({"z": [10.0, 10.0], "x": 10.0, "y2": 10.0}, outputs)
    assert outputs["y1"] == 118.0

    # Get component 2 #########################################################
    # Tests also the transmission of options
    with pytest.raises(FastBadSystemOptionError):
        disc2_component = RegisterOpenMDAOSystem.get_system(
            "module_management_test.sellar.disc2", options={"not_declared": -1}
        )

    disc2_component = RegisterOpenMDAOSystem.get_system(
        "module_management_test.sellar.disc2", options={"answer": -1}
    )
    assert (
        RegisterOpenMDAOSystem.get_provider_domain("module_management_test.sellar.disc2").value
        == ModelDomain.GEOMETRY.value
    )
    assert (
        RegisterOpenMDAOSystem.get_provider_domain(disc2_component).value
        == ModelDomain.GEOMETRY.value
    )
    assert (
        RegisterOpenMDAOSystem.get_provider_description(disc2_component) == RegisteredDisc2.__doc__
    )
    assert (
        disc2_component.options["answer"] == 42
    )  # still the initial value as setup() has not been run
    disc2_component.setup()
    assert disc2_component.options["answer"] == -1
    outputs = {}
    disc2_component.compute({"z": [10.0, 10.0], "y1": 4.0}, outputs)
    assert outputs["y2"] == 22.0

    # Get component 2 bis #####################################################
    # Tests the transmission of options at registration
    with pytest.raises(FastBadSystemOptionError):
        functions_component = RegisterOpenMDAOSystem.get_system(
            "module_management_test.sellar.function_f", options={"not_declared": -1}
        )

    functions_component = RegisterOpenMDAOSystem.get_system(
        "module_management_test.sellar.function_f"
    )
    assert (
        RegisterOpenMDAOSystem.get_provider_domain("module_management_test.sellar.function_f").value
        == ModelDomain.UNSPECIFIED.value
    )
    assert (
        RegisterOpenMDAOSystem.get_provider_domain(functions_component).value
        == ModelDomain.UNSPECIFIED.value
    )
    assert (
        functions_component.options["best_doctor"] == 10
    )  # still the initial value as setup() has not been run
    functions_component.setup()
    assert functions_component.options["best_doctor"] == 11

    # Get unknown component ###################################################
    with pytest.raises(FastBundleLoaderUnknownFactoryNameError):
        RegisterOpenMDAOSystem.get_system("unknown.identifier")


def test_sellar(load):
    """
    Demonstrates usage of RegisterOpenMDAOSystem in a simple Sellar problem
    """

    class SellarComponentProviderByFast(ISellarFactory):
        """
        Provides Sellar components using RegisterOpenMDAOSystem
        """

        def create_disc1(self):
            return RegisterOpenMDAOSystem.get_system("module_management_test.sellar.disc1")

        def create_disc2(self):
            return RegisterOpenMDAOSystem.get_system("module_management_test.sellar.disc2")

        def create_objective_function(self):
            return RegisterOpenMDAOSystem.get_system("module_management_test.sellar.function_f")

        def create_constraints(self):
            constraints = om.Group()
            constraints.add_subsystem(
                "function_g1",
                RegisterOpenMDAOSystem.get_system("module_management_test.sellar.function_g1"),
                promotes=["*"],
            )
            constraints.add_subsystem(
                "function_g2",
                RegisterOpenMDAOSystem.get_system("module_management_test.sellar.function_g2"),
                promotes=["*"],
            )

            return constraints

    classical_problem = BasicSellarProblem(BasicSellarModel())  # Reference
    classical_problem.setup()

    fastoad_problem = BasicSellarProblem(
        BasicSellarModel(sellar_factory=SellarComponentProviderByFast())
    )  # Using RegisterOpenMDAOSystem
    fastoad_problem.setup()

    classical_problem.run_driver()
    assert classical_problem["f"] != fastoad_problem["f"]  # fastoad_problem has not run yet

    fastoad_problem.run_driver()
    assert classical_problem["f"] == fastoad_problem["f"]  # both problems have run
