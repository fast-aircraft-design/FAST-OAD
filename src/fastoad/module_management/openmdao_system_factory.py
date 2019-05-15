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
    __INSTANCE_FIELD_NAME = "__instance__"

    def __init__(self):
        """
        Constructor
        """

    @classmethod
    def get_component(cls, required_properties: dict) -> System:
        """
        Returns the first encountered System instance with properties that match all required properties.
        :param required_properties:
        :return: an OpenMDAO System instance
        """

        loader = Loader()
        components = loader.get_services(SERVICE_OPENMDAO_SYSTEM, required_properties)

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
        loader = Loader()
        context = loader.context
        service_references = loader.get_service_references(SERVICE_OPENMDAO_SYSTEM, required_properties)

        if not service_references:
            raise KeyError(
                'No OpenMDAO system found with these properties: {0}'.format(required_properties))
        else:
            descriptors = [SystemDescriptor(context.get_service(ref), ref.get_properties()) for ref in
                           service_references]
        return descriptors
