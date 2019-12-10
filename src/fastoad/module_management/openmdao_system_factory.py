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
from .bundle_loader import BundleLoader
from .constants import SERVICE_OPENMDAO_SYSTEM
from .exceptions import FastDuplicateFactoryError, \
    FastNoOMSystemFoundError, FastUnknownOMSystemIdentifierError, \
    FastDuplicateOMSystemIdentifierException

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
        :meth:`~OpenMDAOSystemFactory.register_system` )

        :param folder_path:
        """
        cls._loader.install_packages(folder_path)

    @classmethod
    def register_system(cls, system_class: type, identifier: str, properties: dict = None):
        """
        Registers the System (or subclass) so it can later be retrieved and
        instantiated.

        *WARNING:*
        **A System cannot be accessed by** :meth:`~OpenMDAOSystemFactory.get_system`
        **in the Python module where it is registered** (but one normally does not need
        to do that, since in this case, the Python class is directly accessible)

        :param system_class:
        :param identifier:
        :param properties: properties that will be associated to the service
        :raise FastDuplicateOMSystemIdentifierException:
        """
        try:
            cls._loader.register_factory(system_class, identifier, SERVICE_OPENMDAO_SYSTEM,
                                         properties)
        except FastDuplicateFactoryError as err:
            # Just a more specialized error message
            raise FastDuplicateOMSystemIdentifierException(err.factory_name)

    @classmethod
    def get_system_ids(cls, properties: dict = None) -> List[str]:
        """

        :param properties: if provided, only factories that match all provided properties
                           will be returned
        :return: the list of identifiers for registered factories.
        """
        return cls._loader.get_factory_names(SERVICE_OPENMDAO_SYSTEM, properties=properties)

    @classmethod
    def get_system(cls, identifier: str) -> SystemSubclass:
        """

        :param identifier: identifier of the registered class
        :return: an OpenMDAO system instantiated from the registered class
        """

        try:
            system = cls._loader.instantiate_component(identifier)
        except TypeError:
            raise FastUnknownOMSystemIdentifierError(identifier)

        return system

    @classmethod
    def get_systems_from_properties(cls, required_properties: dict) \
            -> List[SystemSubclass]:
        """
        Returns the System instances with properties that
        match all required properties.

        :param required_properties:
        :return: OpenMDAO System (or subclass) instances
        """

        system_ids = cls.get_system_ids(required_properties)
        if not system_ids:
            raise FastNoOMSystemFoundError(required_properties)

        systems = [cls._loader.instantiate_component(id) for id in system_ids]
        return systems
