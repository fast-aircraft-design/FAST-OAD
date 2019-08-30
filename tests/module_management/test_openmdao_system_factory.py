"""
Test module for openmdao_system_factory.py
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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

from openmdao.api import Problem, ScipyOptimizeDriver  # , pyOptSparseDriver

from fastoad.module_management import BundleLoader
from fastoad.module_management.constants import SERVICE_OPENMDAO_SYSTEM
from fastoad.module_management.openmdao_system_factory import OpenMDAOSystemFactory
from tests.sellar_example.sellar import Sellar, ISellarFactory

_LOGGER = logging.getLogger(__name__)
"""Logger for this module"""

logging.basicConfig(level=logging.DEBUG)


def __install_components():
    """
    Loads registered components

    See sellar_example.register_components.py for the registering process
    """

    OpenMDAOSystemFactory.explore_folder(
        pth.join(pth.dirname(__file__), '..', 'sellar_example'))


def test_components_alone():
    """
    Simple test of existence of "openmdao.component" services
    """
    loader = BundleLoader()
    loader.install_packages(pth.join(pth.dirname(__file__), '..', 'sellar_example'))

    services = loader.get_services(SERVICE_OPENMDAO_SYSTEM)
    assert services

    # Pelix framework has to be deleted for next tests to run smoothly
    loader.framework.delete(True)


def test_get_component():
    """
    Tests the retrieval of component according to properties
    """

    __install_components()

    # Get component 1 #########################################################
    disc1_component = OpenMDAOSystemFactory.get_system({'Number': 1})
    assert disc1_component is not None
    disc1_component.setup()
    outputs = {}
    disc1_component.compute({'z': [10., 10.], 'x': 10., 'y2': 10.}, outputs)
    assert outputs['y1'] == 118.

    # Get component 1 #########################################################
    disc2_component = OpenMDAOSystemFactory.get_system({'Number': 2})
    assert disc2_component is not None
    disc2_component.setup()
    outputs = {}
    disc2_component.compute({'z': [10., 10.], 'y1': 4.}, outputs)
    assert outputs['y2'] == 22.

    # Get component when several possible #####################################
    any_component = OpenMDAOSystemFactory.get_system({'Discipline': 'generic'})
    assert any_component is disc1_component or any_component is disc2_component

    # Error raised when property does not exists ##############################
    got_key_error = False
    try:
        OpenMDAOSystemFactory.get_system({'MissingProperty': -5})
    except KeyError:
        got_key_error = True
    assert got_key_error

    # Error raised when no matching component #################################
    got_key_error = False
    try:
        OpenMDAOSystemFactory.get_system({'Number': -5})
    except KeyError:
        got_key_error = True
    assert got_key_error

    # Pelix framework has to be deleted for next tests to run smoothly
    BundleLoader().framework.delete(True)


def test_get_systems():
    """
    Tests the retrieval of component descriptors according to properties
    """
    __install_components()

    # Get component 1 #########################################################
    systems = OpenMDAOSystemFactory.get_systems({'Number': 1})
    assert len(systems) == 1
    disc1_component = systems[0]
    assert disc1_component.Discipline == 'generic'
    assert disc1_component is not None
    disc1_component.setup()
    outputs = {}
    disc1_component.compute({'z': [10., 10.], 'x': 10., 'y2': 10.}, outputs)
    assert outputs['y1'] == 118.

    # Get component when several possible #####################################
    systems = OpenMDAOSystemFactory.get_systems({'Discipline': 'generic'})
    assert len(systems) == 2

    # Error raised when property does not exists ##############################
    got_key_error = False
    try:
        OpenMDAOSystemFactory.get_systems({'MissingProperty': -5})
    except KeyError:
        got_key_error = True
    assert got_key_error

    # Error raised when no matching component #################################
    got_key_error = False
    try:
        OpenMDAOSystemFactory.get_systems({'Number': -5})
    except KeyError:
        got_key_error = True
    assert got_key_error

    # Pelix framework has to be deleted for next tests to run smoothly
    BundleLoader().framework.delete(True)


def test_sellar():
    """
    Demonstrates usage of OpenMDAOSystemFactory in a simple Sellar problem
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

        problem.model.approx_totals()
        problem.model.add_design_var('x', lower=0, upper=10)
        problem.model.add_design_var('z', lower=0, upper=10)

        problem.model.add_objective('f')

        problem.model.add_constraint('g1', upper=0.)
        problem.model.add_constraint('g2', upper=0.)

        problem.setup()

        return problem

    class SellarComponentProviderByFast(ISellarFactory):
        """
        Provides Sellar components using OpenMDAOSystemFactory
        """

        @staticmethod
        def create_disc1():
            return OpenMDAOSystemFactory.get_system({'Number': 1})

        @staticmethod
        def create_disc2():
            return OpenMDAOSystemFactory.get_system({'Number': 2})

        @staticmethod
        def create_functions():
            return OpenMDAOSystemFactory.get_system({'Discipline': 'function'})

    __install_components()

    classical_problem = sellar_setup(Sellar())  # Reference
    fastoad_problem = sellar_setup(
        Sellar(SellarComponentProviderByFast))  # Using OpenMDAOSystemFactory

    classical_problem.run_driver()
    assert classical_problem['f'] != fastoad_problem['f']  # fastoad_problem has not run yet

    fastoad_problem.run_driver()
    assert classical_problem['f'] == fastoad_problem['f']  # both problems have run


if __name__ == "__main__":
    test_sellar()
