"""
Test module for openmdao_system_factory.py
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

import logging
import os.path as pth

import pytest
from openmdao.api import Problem, ScipyOptimizeDriver  # , pyOptSparseDriver

from fastoad.module_management import BundleLoader
from fastoad.module_management.constants import SERVICE_OPENMDAO_SYSTEM
from fastoad.module_management.exceptions import FastNoOMSystemFoundError, \
    FastUnknownOMSystemIdentifierError, FastBadSystemOptionError
from fastoad.module_management import OpenMDAOSystemRegistry
from tests import root_folder_path
from tests.sellar_example.sellar import Sellar, ISellarFactory

_LOGGER = logging.getLogger(__name__)
"""Logger for this module"""

logging.basicConfig(level=logging.DEBUG)


# pylint: disable=redefined-outer-name  # pytest fixture
# pylint: disable=unused-argument  # pytest fixture

@pytest.fixture()
def framework_load_unload():
    """ Loads and unloads Pelix framework for each test """
    # Starts Pelix framework and load components
    OpenMDAOSystemRegistry.explore_folder(pth.join(root_folder_path, 'tests', 'sellar_example'))
    yield

    # Pelix framework has to be deleted for following tests to run smoothly
    BundleLoader().framework.delete(True)


def test_components_alone(framework_load_unload):
    """
    Simple test of existence of "openmdao.component" service factories
    """

    services = BundleLoader().get_factory_names(SERVICE_OPENMDAO_SYSTEM)
    assert services


def test_get_system(framework_load_unload):
    """
    Tests the retrieval of a System according to identifier
    """

    # Get component 1 #########################################################
    disc1_component = OpenMDAOSystemRegistry.get_system('sellar.disc1')
    assert disc1_component._Discipline == 'generic'  # pylint: disable=protected-access
    assert disc1_component is not None
    disc1_component.setup()
    outputs = {}
    disc1_component.compute({'z': [10., 10.], 'x': 10., 'y2': 10.}, outputs)
    assert outputs['y1'] == 118.

    # Get component 2 #########################################################
    with pytest.raises(FastBadSystemOptionError):
        disc2_component = OpenMDAOSystemRegistry.get_system('sellar.disc2',
                                                            options={'not_declared': -1})

    disc2_component = OpenMDAOSystemRegistry.get_system('sellar.disc2', options={'answer': -1})
    assert disc2_component.options[
               'answer'] == 42  # still the intial value as setup() has not been run
    disc2_component.setup()
    assert disc2_component.options['answer'] == -1
    outputs = {}
    disc2_component.compute({'z': [10., 10.], 'y1': 4.}, outputs)
    assert outputs['y2'] == 22.

    # Get unknown component
    with pytest.raises(FastUnknownOMSystemIdentifierError):
        OpenMDAOSystemRegistry.get_system('unknown.identifier')


def test_get_systems_from_properties(framework_load_unload):
    """
    Tests the retrieval of OpenMDAO systems according to properties
    """

    # Get component 1 #########################################################
    systems = OpenMDAOSystemRegistry.get_systems_from_properties({'Number': 1})
    assert len(systems) == 1
    disc1_component = systems[0]
    assert disc1_component._Discipline == 'generic'  # pylint: disable=protected-access
    assert disc1_component is not None
    disc1_component.setup()
    outputs = {}
    disc1_component.compute({'z': [10., 10.], 'x': 10., 'y2': 10.}, outputs)
    assert outputs['y1'] == 118.

    # Get component 2 #########################################################
    systems = OpenMDAOSystemRegistry.get_systems_from_properties({'Number': 2})
    assert len(systems) == 1
    disc2_component = systems[0]
    assert disc2_component is not None
    disc2_component.setup()
    outputs = {}
    disc2_component.compute({'z': [10., 10.], 'y1': 4.}, outputs)
    assert outputs['y2'] == 22.

    # Get component when several possible #####################################
    systems = OpenMDAOSystemRegistry.get_systems_from_properties({'Discipline': 'generic'})
    assert len(systems) == 2

    # Error raised when property does not exists ##############################
    with pytest.raises(FastNoOMSystemFoundError):
        OpenMDAOSystemRegistry.get_systems_from_properties({'MissingProperty': -5})

    # Error raised when no matching component #################################
    with pytest.raises(FastNoOMSystemFoundError):
        OpenMDAOSystemRegistry.get_systems_from_properties({'Number': -5})


def test_sellar(framework_load_unload):
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

        problem.driver.options['optimizer'] = 'SLSQP'
        problem.driver.options['tol'] = 1.0e-08
        # pb.driver.options['maxiter'] = 100
        problem.driver.options['disp'] = True

        problem.model.add_design_var('x', lower=0, upper=10)
        problem.model.add_design_var('z', lower=0, upper=10)

        problem.model.add_objective('f')

        problem.model.add_constraint('g1', upper=0.)
        problem.model.add_constraint('g2', upper=0.)

        problem.setup()

        return problem

    class SellarComponentProviderByFast(ISellarFactory):
        """
        Provides Sellar components using OpenMDAOSystemRegistry
        """

        @staticmethod
        def create_disc1():
            return OpenMDAOSystemRegistry.get_system('sellar.disc1')

        @staticmethod
        def create_disc2():
            return OpenMDAOSystemRegistry.get_system('sellar.disc2')

        @staticmethod
        def create_functions():
            return OpenMDAOSystemRegistry.get_system('sellar.functions')

    classical_problem = sellar_setup(Sellar())  # Reference
    fastoad_problem = sellar_setup(
        Sellar(SellarComponentProviderByFast))  # Using OpenMDAOSystemRegistry

    classical_problem.run_driver()
    assert classical_problem['f'] != fastoad_problem['f']  # fastoad_problem has not run yet

    fastoad_problem.run_driver()
    assert classical_problem['f'] == fastoad_problem['f']  # both problems have run
