"""Exceptions for module_management package."""
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

from fastoad.exceptions import FastError


class FastDuplicateFactoryError(FastError):
    def __init__(self, factory_name):
        """
        Raised when trying to register a factory with an already used name.

        :param factory_name:
        """
        super().__init__('Name "%s" is already used.' % factory_name)
        self.factory_name = factory_name


class FastDuplicateOMSystemIdentifierException(FastDuplicateFactoryError):
    """
    Raised when trying to register an OpenMDAO System with an already used identifier.
    """

    def __str__(self):
        """

        :return:
        """
        return (
            "Tried to register an OpenMDAO system with an already used identifier : %s"
            % self.factory_name
        )


class FastNoOMSystemFoundError(FastError):
    def __init__(self, properties):
        """
        Raised when no registered OpenMDAO system could be found from asked properties.

        :param properties:
        """
        super().__init__("No OpenMDAO system found with these properties: %s" % properties)
        self.properties = properties


class FastUnknownOMSystemIdentifierError(FastError):
    def __init__(self, identifier):
        """
        Raised when no OpenMDAO system is registered with asked identifier.

        :param identifier:
        """
        super().__init__("No OpenMDAO system found with this identifier: %s" % identifier)
        self.identifier = identifier


class FastBadSystemOptionError(FastError):
    def __init__(self, identifier, option_names):
        """
        Raised when some option name is not conform to OpenMDAO system definition.

        :param identifier: system identifier
        :param option_names: incorrect option names
        """
        super().__init__(
            "OpenMDAO system %s does not accept following option(s): %s"
            % (identifier, option_names)
        )
        self.identifier = identifier
        self.option_names = option_names


class FastIncompatibleServiceClass(FastError):
    """"""

    def __init__(self, registered_class: type, service_id: str, base_class: type):
        """
        Raised when trying to register as service a class that does not implement
        the specified interface.

        :param registered_class:
        :param service_id:
        :param base_class: the unmatched interface
        """
        super().__init__(
            'Trying to register %s as service "%s" but it does not inherit from %s'
            % (str(registered_class), service_id, str(base_class))
        )
        self.registered_class = registered_class
        self.service_id = service_id
        self.base_class = base_class
