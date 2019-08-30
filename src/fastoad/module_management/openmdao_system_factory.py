# -*- coding: utf-8 -*-
"""
The base layer for registering and retrieving OpenMDAO systems
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
from typing import List, TypeVar

from openmdao.core.system import System

from . import BundleLoader
from .constants import SERVICE_OPENMDAO_SYSTEM

_LOGGER = logging.getLogger(__name__)
"""Logger for this module"""

from fastoad.openmdao.types import SystemSubclass


class OpenMDAOSystemFactory:
    """
    Class for providing OpenMDAO System objects depending on their properties.
    """
    __loader = BundleLoader()

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
        Registers the System (or subclass) instance as a service so it can
        later be retrieved.

        :param system:
        :param properties: properties that will be associated to the service
        """
        cls.__loader.context.register_service(SERVICE_OPENMDAO_SYSTEM
                                              , system, properties)

    @classmethod
    def get_system(cls, required_properties: dict) -> SystemSubclass:
        """
        Returns the first encountered System instance with properties that
        match all required properties.

        :param required_properties:
        :return: an OpenMDAO System instance
        """

        components = cls.__loader.get_services(SERVICE_OPENMDAO_SYSTEM
                                               , required_properties)

        if not components:
            raise KeyError(
                'No OpenMDAO system found with these properties'
                ': %s' % required_properties)

        if len(components) > 1:
            _LOGGER.warning('More than one OpenMDAO system found with these '
                            'properties: %s', required_properties)
            _LOGGER.warning('Returning first one.')
        return components[0]

    @classmethod
    def get_systems(cls, required_properties: dict) \
            -> List[SystemSubclass]:
        """
        Returns the first encountered System instance with properties that
        match all required properties.

        :param required_properties:
        :return: an OpenMDAO SystemDescriptor
        """
        context = cls.__loader.context
        service_references = cls.__loader.get_service_references(
            SERVICE_OPENMDAO_SYSTEM
            , required_properties)

        if not service_references:
            raise KeyError(
                'No OpenMDAO system found with these properties: %s'
                % required_properties)

        descriptors = [context.get_service(ref) for ref in service_references]
        return descriptors
