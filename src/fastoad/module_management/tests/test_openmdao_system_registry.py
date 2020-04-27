"""
Test module for openmdao_system_registry.py
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
import os.path as pth

import pytest
from openmdao.api import Problem, ScipyOptimizeDriver

from .sellar_example.disc2 import Disc2
from .sellar_example.sellar import Sellar, ISellarFactory
from .. import BundleLoader
from .. import OpenMDAOSystemRegistry as Registry
from ..constants import SERVICE_OPENMDAO_SYSTEM, ModelDomain
from ..exceptions import FastUnknownOMSystemIdentifierError, FastBadSystemOptionError

_LOGGER = logging.getLogger(__name__)
"""Logger for this module"""

logging.basicConfig(level=logging.DEBUG)


# pylint: disable=redefined-outer-name  # pytest fixture
# pylint: disable=unused-argument  # pytest fixture


@pytest.fixture(scope="module")
def load():
    """ Loads components """
    Registry.explore_folder(pth.join(pth.dirname(__file__), "sellar_example"))


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
    disc1_component = Registry.get_system("sellar.disc1")
    assert Registry.get_system_domain("sellar.disc1").value == ModelDomain.OTHER.value
    assert Registry.get_system_domain(disc1_component).value == ModelDomain.OTHER.value
    assert Registry.get_system_description(disc1_component) == "some text"
    assert disc1_component is not None
    disc1_component.setup()
    outputs = {}
    disc1_component.compute({"z": [10.0, 10.0], "x": 10.0, "y2": 10.0}, outputs)
    assert outputs["y1"] == 118.0

    # Get component 2 #########################################################
    # Tests also the transmission of options
    with pytest.raises(FastBadSystemOptionError):
        disc2_component = Registry.get_system("sellar.disc2", options={"not_declared": -1})

    disc2_component = Registry.get_system("sellar.disc2", options={"answer": -1})
    assert Registry.get_system_domain("sellar.disc2").value == ModelDomain.GEOMETRY.value
    assert Registry.get_system_domain(disc2_component).value == ModelDomain.GEOMETRY.value
    assert Registry.get_system_description(disc2_component) == Disc2.__doc__
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
        functions_component = Registry.get_system("sellar.functions", options={"not_declared": -1})

    functions_component = Registry.get_system("sellar.functions")
    assert Registry.get_system_domain("sellar.functions").value == ModelDomain.UNSPECIFIED.value
    assert Registry.get_system_domain(functions_component).value == ModelDomain.UNSPECIFIED.value
    assert (
        functions_component.options["best_doctor"] == 10
    )  # still the initial value as setup() has not been run
    functions_component.setup()
    assert functions_component.options["best_doctor"] == 11

    # Get unknown component ###################################################
    with pytest.raises(FastUnknownOMSystemIdentifierError):
        Registry.get_system("unknown.identifier")


def test_sellar(load):
    """
    Demonstrates usage of OpenMDAOSystemRegistry in a simple Sellar problem
    """

    def sellar_setup(sellar_instance: Sellar):
        """
        Sets up the Sellar problem, given a Sellar Group() instance.

        Pure OpenMDAO scripting.
        """
        problem = Problem()
        problem.model = sellar_instance

        problem.driver = ScipyOptimizeDriver()

        problem.driver.options["optimizer"] = "SLSQP"
        problem.driver.options["tol"] = 1.0e-08
        # pb.driver.options['maxiter'] = 100
        problem.driver.options["disp"] = True

        problem.model.add_design_var("x", lower=0, upper=10)
        problem.model.add_design_var("z", lower=0, upper=10)

        problem.model.add_objective("f")

        problem.model.add_constraint("g1", upper=0.0)
        problem.model.add_constraint("g2", upper=0.0)

        problem.setup()

        return problem

    class SellarComponentProviderByFast(ISellarFactory):
        """
        Provides Sellar components using OpenMDAOSystemRegistry
        """

        @staticmethod
        def create_disc1():
            return Registry.get_system("sellar.disc1")

        @staticmethod
        def create_disc2():
            return Registry.get_system("sellar.disc2")

        @staticmethod
        def create_functions():
            return Registry.get_system("sellar.functions")

    classical_problem = sellar_setup(Sellar())  # Reference
    fastoad_problem = sellar_setup(
        Sellar(SellarComponentProviderByFast)
    )  # Using OpenMDAOSystemRegistry

    classical_problem.run_driver()
    assert classical_problem["f"] != fastoad_problem["f"]  # fastoad_problem has not run yet

    fastoad_problem.run_driver()
    assert classical_problem["f"] == fastoad_problem["f"]  # both problems have run
