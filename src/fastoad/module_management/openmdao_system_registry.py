"""
The base layer for registering and retrieving OpenMDAO systems
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
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
import warnings
from typing import List, Union, Any

from fastoad.openmdao.types import SystemSubclass
from .bundle_loader import BundleLoader
from .constants import (
    SERVICE_OPENMDAO_SYSTEM,
    OPTION_PROPERTY_NAME,
    DESCRIPTION_PROPERTY_NAME,
    DOMAIN_PROPERTY_NAME,
    ModelDomain,
)
from .exceptions import FastBadSystemOptionError
from .service_registry import _option_decorator

_LOGGER = logging.getLogger(__name__)
"""Logger for this module"""


class OpenMDAOSystemRegistry:
    """
    Class for registering and providing OpenMDAO System objects.
    """

    _loader = BundleLoader()

    @classmethod
    def explore_folder(cls, folder_path: str):
        """
        Explores provided folder for Systems to register (i.e. modules that use
        :meth:`~OpenMDAOSystemRegistry.register_system` )

        :param folder_path:
        """
        warnings.warn(
            "OpenMDAOSystemRegistry will be removed in version 1.0. "
            "Please use RegisterOpenMDAOSystem decorator instead.",
            DeprecationWarning,
        )

        cls._loader.explore_folder(folder_path)

    @classmethod
    def register_system(
        cls,
        system_class: type,
        identifier: str,
        domain: ModelDomain = None,
        desc=None,
        options: dict = None,
    ):
        """
        Registers the System (or subclass) so it can later be retrieved and
        instantiated.

        :param system_class:
        :param identifier:
        :param domain: information about model domain
        :param desc: description of the model. If not provided, the docstring of
                     the class will be used.
        :param options: options to be transmitted to OpenMDAO class at run-time
        :raise FastDuplicateOMSystemIdentifierException:
        """

        warnings.warn(
            "OpenMDAOSystemRegistry will be removed in version 1.0. "
            "Please use RegisterOpenMDAOSystem decorator instead.",
            DeprecationWarning,
        )

        properties = {
            DOMAIN_PROPERTY_NAME: domain if domain else ModelDomain.UNSPECIFIED,
            DESCRIPTION_PROPERTY_NAME: desc if desc else system_class.__doc__,
            OPTION_PROPERTY_NAME: options if options else {},
        }
        factory = cls._loader.register_factory(
            system_class, identifier, SERVICE_OPENMDAO_SYSTEM, properties
        )
        return factory

    @classmethod
    def get_system_ids(cls, properties: dict = None) -> List[str]:
        """

        :param properties: if provided, only factories that match all provided properties
                           will be returned
        :return: the list of identifiers for registered factories.
        """
        warnings.warn(
            "OpenMDAOSystemRegistry will be removed in version 1.0. "
            "Please use RegisterOpenMDAOSystem decorator instead.",
            DeprecationWarning,
        )

        return cls._loader.get_factory_names(SERVICE_OPENMDAO_SYSTEM, properties=properties)

    @classmethod
    def get_system(cls, identifier: str, options: dict = None) -> SystemSubclass:
        """

        :param identifier: identifier of the registered class
        :param options: option values at system instantiation
        :return: an OpenMDAO system instantiated from the registered class
        """
        warnings.warn(
            "OpenMDAOSystemRegistry will be removed in version 1.0. "
            "Please use RegisterOpenMDAOSystem decorator instead.",
            DeprecationWarning,
        )

        properties = cls._loader.get_factory_properties(identifier).copy()

        if options:
            properties[OPTION_PROPERTY_NAME] = properties[OPTION_PROPERTY_NAME].copy()
            properties[OPTION_PROPERTY_NAME].update(options)

        system = cls._loader.instantiate_component(identifier, properties=properties)

        # Before making the system available to get options from OPTION_PROPERTY_NAME,
        # check that options are valid to avoid failure at setup()
        options = getattr(system, "_" + OPTION_PROPERTY_NAME, None)
        if options:
            invalid_options = [name for name in options if name not in system.options]
            if invalid_options:
                raise FastBadSystemOptionError(identifier, invalid_options)

        decorated_system = _option_decorator(system)
        return decorated_system

    @classmethod
    def get_system_domain(cls, system_or_id: Union[str, SystemSubclass]) -> ModelDomain:
        """

        :param system_or_id: an identifier of a registered OpenMDAO System class or
                             an instance of a registered OpenMDAO System class
        :return: the model domain associated to given system or system identifier
        """
        warnings.warn(
            "OpenMDAOSystemRegistry will be removed in version 1.0. "
            "Please use RegisterOpenMDAOSystem decorator instead.",
            DeprecationWarning,
        )

        return cls._get_system_property(system_or_id, DOMAIN_PROPERTY_NAME)

    @classmethod
    def get_system_description(cls, system_or_id: Union[str, SystemSubclass]) -> str:
        """

        :param system_or_id: an identifier of a registered OpenMDAO System class or
                             an instance of a registered OpenMDAO System class
        :return: the description associated to given system or system identifier
        """
        warnings.warn(
            "OpenMDAOSystemRegistry will be removed in version 1.0. "
            "Please use RegisterOpenMDAOSystem decorator instead.",
            DeprecationWarning,
        )

        return cls._get_system_property(system_or_id, DESCRIPTION_PROPERTY_NAME)

    @classmethod
    def _get_system_property(
        cls, system_or_id: Union[str, SystemSubclass], property_name: str
    ) -> Any:
        """

        :param system_or_id: an identifier of a registered OpenMDAO System class or
                             an instance of a registered OpenMDAO System class
        :param property_name:
        :return: the property value associated to given system or system identifier
        """
        warnings.warn(
            "OpenMDAOSystemRegistry will be removed in version 1.0. "
            "Please use RegisterOpenMDAOSystem decorator instead.",
            DeprecationWarning,
        )

        if isinstance(system_or_id, str):
            return BundleLoader().get_factory_property(system_or_id, property_name)
        else:
            return BundleLoader().get_instance_property(system_or_id, property_name)
