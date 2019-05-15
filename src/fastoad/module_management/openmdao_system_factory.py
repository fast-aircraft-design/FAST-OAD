#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from typing import List, TypeVar

from openmdao.core.system import System

from .bundle_loader import Loader
from .constants import SERVICE_OPENMDAO_SYSTEM

_logger = logging.getLogger(__name__)
"""Logger for this module"""

SystemSubclass = TypeVar('SystemSubclass', bound=System)


class SystemDescriptor:
    """
    Simple wrapper class for associating an OpenMDAO System instance and its user-defined metadata
    """

    def __init__(self, component: SystemSubclass, properties: dict = {}):
        self._component = component
        self._properties = properties

    def get_system(self) -> SystemSubclass:
        return self._component

    def get_properties(self) -> dict:
        return self._properties


class OpenMDAOSystemFactory:
    """
    Class for providing OpenMDAO System objects depending on their properties.
    """
    __loader = Loader()

    @classmethod
    def explore_folder(cls, folder_path: str):
        """
        Explores provided folder for Systems to register (i.e. modules that use
        OpenMDAOSystemFactory.register_component() )

        :param folder_path:
        """
        cls.__loader.install_packages(folder_path)

    @classmethod
    def register_system(cls, system: SystemSubclass, properties: dict):
        """
        Registers the System (or subclass) instance as a service so it can later be retrieved.

        :param system:
        :param properties: properties that will be associated to the service
        """
        cls.__loader.context.register_service(SERVICE_OPENMDAO_SYSTEM, system, properties)

    @classmethod
    def get_system(cls, required_properties: dict) -> SystemSubclass:
        """
        Returns the first encountered System instance with properties that match all required properties.
        :param required_properties:
        :return: an OpenMDAO System instance
        """

        components = cls.__loader.get_services(SERVICE_OPENMDAO_SYSTEM, required_properties)

        if not components:
            raise KeyError(
                'No OpenMDAO system found with these properties: {0}'.format(required_properties))
        else:
            if len(components) > 1:
                _logger.warning("More than one OpenMDAO system found with these properties: {0}")
                _logger.warning("Returning first one.")
            return components[0]

    @classmethod
    def get_system_descriptors(cls, required_properties: dict) -> List[SystemDescriptor]:
        """
        Returns the first encountered System instance with properties that match all required properties.
        :param required_properties:
        :return: an OpenMDAO SystemDescriptor
        """
        context = cls.__loader.context
        service_references = cls.__loader.get_service_references(SERVICE_OPENMDAO_SYSTEM, required_properties)

        if not service_references:
            raise KeyError(
                'No OpenMDAO system found with these properties: {0}'.format(required_properties))
        else:
            descriptors = [SystemDescriptor(context.get_service(ref), ref.get_properties()) for ref in
                           service_references]
        return descriptors
