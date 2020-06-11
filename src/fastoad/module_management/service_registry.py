"""Module for registering services."""
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

from fastoad.models.propulsion import IOMPropulsionWrapper
from fastoad.module_management.constants import SERVICE_PROPULSION_WRAPPER
from fastoad.module_management.exceptions import FastIncompatibleServiceClass
from pelix.ipopo.decorators import ComponentFactory, Provides


class RegisterService:
    def __init__(self, provider_id: str, service_id: str, base_class: type = None):
        """
        Decorator class that allows to register a service.

        The service can be associated to a base class (or interface). Then all registered
        classes must inherit from this base class.

        Warning: the module must be started as an iPOPO bundle for the decorator to work.

        :param provider_id: the identifier of the service provider to register
        :param service_id: the identifier of the service
        :param base_class: the class that should be parent to the registered class
        """
        self._id = provider_id
        self._service_id = service_id
        self._base_class = base_class

    def __call__(self, service_class: type) -> type:
        if self._base_class and not issubclass(service_class, self._base_class):
            raise FastIncompatibleServiceClass(service_class, self._service_id, self._base_class)

        return ComponentFactory(self._id)(Provides(self._service_id)(service_class))


class RegisterPropulsion(RegisterService):
    def __init__(self, model_id):
        """
        Decorator class for registering a propulsion-dedicated model.

        Warning: the module must be started as an iPOPO bundle for the decorator to work.

        :param model_id: the identifier of the propulsion model
        """
        super().__init__(model_id, SERVICE_PROPULSION_WRAPPER, IOMPropulsionWrapper)
