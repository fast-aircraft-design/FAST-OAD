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
from typing import List

from fastoad.openmdao.types import SystemSubclass
from . import BundleLoader
from .constants import SERVICE_OPENMDAO_SYSTEM

_LOGGER = logging.getLogger(__name__)
"""Logger for this module"""


class OpenMDAOSystemFactory:
    """
    Class for providing OpenMDAO System objects depending on their properties.
    """
    _loader = BundleLoader()

    @classmethod
    def explore_folder(cls, folder_path: str):
        """
        Explores provided folder for Systems to register (i.e. modules that use
        OpenMDAOSystemFactory.register_component() )

        :param folder_path:
        """
        cls._loader.install_packages(folder_path)

    @classmethod
    def register_system(cls, system_class: type, identifier: str, properties: dict = None):
        """
        Registers the System (or subclass) so it can later be retrieved and
        instantiated.

        :param system_class:
        :param identifier:
        :param properties: properties that will be associated to the service
        """
        cls._loader.register_factory(system_class, identifier, SERVICE_OPENMDAO_SYSTEM, properties)

    @classmethod
    def get_system(cls, identifier: str) -> SystemSubclass:
        """

        :param identifier:
        :return:
        """

        return cls._loader.instantiate_component(identifier)

    @classmethod
    def get_system_from_properties(cls, required_properties: dict) -> SystemSubclass:
        """
        Returns the first encountered System instance with properties that
        match all required properties.

        :param required_properties:
        :return: an OpenMDAO System (or subclass) instance
        """

        factory_names = cls._get_system_factory_names(required_properties)

        if len(factory_names) > 1:
            _LOGGER.warning('More than one OpenMDAO system found with these '
                            'properties: %s', required_properties)
            _LOGGER.warning('Returning first one.')
        return cls._loader.instantiate_component(factory_names[0])

    @classmethod
    def get_systems_from_properties(cls, required_properties: dict) \
            -> List[SystemSubclass]:
        """
        Returns the System instances with properties that
        match all required properties.

        :param required_properties:
        :return: OpenMDAO System (or subclass) instances
        """

        factory_names = cls._get_system_factory_names(required_properties)
        systems = [cls._loader.instantiate_component(name) for name in factory_names]
        return systems

    @classmethod
    def _get_system_factory_names(cls, required_properties: dict) \
            -> List[str]:
        """

        :param required_properties:
        :return: the list of OpenMDAO factory names that match required_properties
        """

        factory_names = cls._loader.get_factory_names(SERVICE_OPENMDAO_SYSTEM, required_properties)

        if not factory_names:
            raise KeyError(
                'No OpenMDAO system found with these properties'
                ': %s' % required_properties)

        return factory_names
