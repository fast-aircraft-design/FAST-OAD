"""
The base layer for registering and retrieving OpenMDAO systems
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
from types import MethodType
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
from .exceptions import (
    FastDuplicateFactoryError,
    FastUnknownOMSystemIdentifierError,
    FastDuplicateOMSystemIdentifierException,
    FastBadSystemOptionError,
)

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
        cls._loader.install_packages(folder_path)

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
        try:
            properties = {
                DOMAIN_PROPERTY_NAME: domain if domain else ModelDomain.UNSPECIFIED,
                DESCRIPTION_PROPERTY_NAME: desc if desc else system_class.__doc__,
                OPTION_PROPERTY_NAME: options if options else {},
            }
            factory = cls._loader.register_factory(
                system_class, identifier, SERVICE_OPENMDAO_SYSTEM, properties
            )
            return factory
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
    def get_system(cls, identifier: str, options: dict = None) -> SystemSubclass:
        """

        :param identifier: identifier of the registered class
        :param options: option values at system instantiation
        :return: an OpenMDAO system instantiated from the registered class
        """

        try:
            properties = cls._loader.get_factory_properties(identifier).copy()
        except ValueError:
            raise FastUnknownOMSystemIdentifierError(identifier)

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
        return cls._get_system_property(system_or_id, DOMAIN_PROPERTY_NAME)

    @classmethod
    def get_system_description(cls, system_or_id: Union[str, SystemSubclass]) -> str:
        """

        :param system_or_id: an identifier of a registered OpenMDAO System class or
                             an instance of a registered OpenMDAO System class
        :return: the description associated to given system or system identifier
        """

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

        if isinstance(system_or_id, str):
            return BundleLoader().get_factory_property(system_or_id, property_name)
        else:
            return BundleLoader().get_instance_property(system_or_id, property_name)


def _option_decorator(instance: SystemSubclass) -> SystemSubclass:
    """
    Decorates provided OpenMDAO instance so that instance.options are populated
    using iPOPO property named after OPTION_PROPERTY_NAME constant.

    :param instance: the instance to decorate
    :return: the decorated instance
    """

    # Rationale:
    #   The idea here is to populate the options at `setup()` time while keeping
    #   all the operations that are in the original `setup()` of the class.
    #
    #   This could have been done by making all our OpenMDAO classes inherit from
    #   a base class where the option values are retrieved, but modifying each
    #   OpenMDAO class looks overkill. Moreover, it would add to them a dependency
    #   to FAST-OAD after having avoided to introduce dependencies outside OpenMDAO.
    #   Last but not least, we would need future contributor to stick to this practice
    #   of inheritance.
    #
    #   Therefore, the most obvious alternative is a decorator. In this decorator, we
    #   could have produced a new instance of the same class that has its own `setup()`
    #   that calls the original `setup()` (i.e. the original Decorator pattern AIUI)
    #   but the new instance would be out of iPOPO's scope.
    #   So we just modify the original instance where we need to "replace"
    #   the `setup()` method to have our code called automagically, without losing the
    #   initial code of `setup()` where there is probably important things. So the trick
    #   is to rename the original `setup()` as `original_setup()`, and create a new
    #   `setup()` that does its job and then calls `original_setup()`.

    def setup(self):
        """ Will replace the original setup() method"""

        # Use values from iPOPO option properties
        option_dict = getattr(self, "_" + OPTION_PROPERTY_NAME, None)
        if option_dict:
            for name, value in option_dict.items():
                self.options[name] = value

        # Call the original setup method
        self.__setup_before_option_decorator()

    # Move the (already bound) method "setup" to "__setup_before_option_decorator"
    setattr(instance, "__setup_before_option_decorator", instance.setup)

    # Create and bind the new "setup" method
    setup_method = MethodType(setup, instance)
    setattr(instance, "setup", setup_method)

    return instance
