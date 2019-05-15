#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os.path as pth

from fastoad.module_management import bundle_loader
from fastoad.module_management.constants import SERVICE_OPENMDAO_SYSTEM
# noinspection PyUnresolvedReferences
# This import is needed for coverage report, though not explicitly used in this module
from fastoad.module_management.openmdao_system_factory import OpenMDAOSystemFactory

_logger = logging.getLogger(__name__)
"""Logger for this module"""

logging.basicConfig(level=logging.DEBUG)


def __install_component_packages(loader: bundle_loader.Loader):
    """
    Uses provided loader for loading needed components
    :param loader:
    :return:
    """

    loader.install_packages(pth.join(pth.dirname(__file__), "sellar_example"))


def test_components_alone():
    """
    Simple test of existence of "openmdao.component" services
    :return:
    """
    loader = bundle_loader.Loader()
    __install_component_packages(loader)

    services = loader.get_services(SERVICE_OPENMDAO_SYSTEM)
    assert services

    # Pelix framework has to be deleted for next tests to run smoothly
    loader.framework.delete(True)


def test_get_component():
    """
    Tests the retrieval of component according to properties
    """
    loader = bundle_loader.Loader()
    __install_component_packages(loader)

    # Get component 1 ##################################################################################################
    disc1_component = OpenMDAOSystemFactory.get_component({"Number": 1})
    assert disc1_component is not None
    disc1_component.setup()
    outputs = {}
    disc1_component.compute({'z': [10., 10.], 'x': 10., 'y2': 10.}, outputs)
    assert outputs['y1'] == 118.

    # Get component 1 ##################################################################################################
    disc2_component = OpenMDAOSystemFactory.get_component({"Number": 2})
    assert disc2_component is not None
    disc2_component.setup()
    outputs = {}
    disc2_component.compute({'z': [10., 10.], 'y1': 4.}, outputs)
    assert outputs['y2'] == 22.

    # Get component when several possible ##############################################################################
    any_component = OpenMDAOSystemFactory.get_component({"Discipline": "generic"})
    assert any_component is disc1_component or any_component is disc2_component

    # Error raised when property does not exists #######################################################################
    got_key_error = False
    try:
        OpenMDAOSystemFactory.get_component({"MissingProperty": -5})
    except KeyError:
        got_key_error = True
    assert got_key_error

    # Error raised when no matching component ##########################################################################
    got_key_error = False
    try:
        OpenMDAOSystemFactory.get_component({"Number": -5})
    except KeyError:
        got_key_error = True
    assert got_key_error

    # Pelix framework has to be deleted for next tests to run smoothly
    loader.framework.delete(True)


def test_get_component_descriptors():
    """
    Tests the retrieval of component descriptors according to properties
    """
    loader = bundle_loader.Loader()
    __install_component_packages(loader)

    # Get component 1 ##################################################################################################
    component_descriptors = OpenMDAOSystemFactory.get_system_descriptors({"Number": 1})
    assert len(component_descriptors) == 1
    disc1_component = component_descriptors[0].get_system()
    assert component_descriptors[0].get_properties()["Discipline"] == "generic"
    assert disc1_component is not None
    disc1_component.setup()
    outputs = {}
    disc1_component.compute({'z': [10., 10.], 'x': 10., 'y2': 10.}, outputs)
    assert outputs['y1'] == 118.

    # Get component when several possible ##############################################################################
    component_descriptors = OpenMDAOSystemFactory.get_system_descriptors({"Discipline": "generic"})
    assert len(component_descriptors) == 2

    # Error raised when property does not exists #######################################################################
    got_key_error = False
    try:
        OpenMDAOSystemFactory.get_system_descriptors({"MissingProperty": -5})
    except KeyError:
        got_key_error = True
    assert got_key_error

    # Error raised when no matching component ##########################################################################
    got_key_error = False
    try:
        OpenMDAOSystemFactory.get_system_descriptors({"Number": -5})
    except KeyError:
        got_key_error = True
    assert got_key_error

    # Pelix framework has to be deleted for next tests to run smoothly
    loader.framework.delete(True)
