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

from typing import List

from pelix.ipopo.decorators import ComponentFactory, Provides, Property

from fastoad.models.propulsion import IOMPropulsionWrapper
from fastoad.module_management import BundleLoader
from fastoad.module_management.constants import (
    SERVICE_PROPULSION_WRAPPER,
    DESCRIPTION_PROPERTY_NAME,
)
from fastoad.module_management.exceptions import FastIncompatibleServiceClass


class RegisterService:
    # FIXME: the content of this class and of OpenMDAOSystemRegistry should be unified.
    def __init__(self, provider_id: str, service_id: str, base_class: type = None, desc=None):
        """
        Decorator class that allows to register a service.

        The service can be associated to a base class (or interface). Then all registered
        classes must inherit from this base class.

        Warning: the module must be started as an iPOPO bundle for the decorator to work.

        :param provider_id: the identifier of the service provider to register
        :param service_id: the identifier of the service
        :param base_class: the class that should be parent to the registered class
        :param desc: description of the service. If not provided, the docstring will be used.
        """
        self._id = provider_id
        self._service_id = service_id
        self._base_class = base_class
        self._desc = desc

    def __call__(self, service_class: type) -> type:
        if self._base_class and not issubclass(service_class, self._base_class):
            raise FastIncompatibleServiceClass(service_class, self._service_id, self._base_class)

        if self._desc:
            prop = Property(DESCRIPTION_PROPERTY_NAME, None, self._desc)
        else:
            prop = Property(DESCRIPTION_PROPERTY_NAME, None, service_class.__doc__)

        return ComponentFactory(self._id)(prop(Provides(self._service_id)(service_class)))

    @classmethod
    def get_service_description(cls, service_id: str) -> str:
        """

        :param service_id: an identifier of a registered service
        :return: the description associated to given system or system identifier
        """

        return BundleLoader().get_factory_property(service_id, DESCRIPTION_PROPERTY_NAME)


class RegisterPropulsion(RegisterService):
    def __init__(self, model_id, desc=None):
        """
        Decorator class for registering a propulsion-dedicated model.

        Warning: the module must be started as an iPOPO bundle for the decorator to work.

        :param model_id: the identifier of the propulsion model
        :param desc: description of the model. If not provided, the docstring will be used.
        """
        super().__init__(model_id, SERVICE_PROPULSION_WRAPPER, IOMPropulsionWrapper, desc=desc)

    @classmethod
    def get_model_ids(cls) -> List[str]:
        """

        :return: the list of identifiers for registered propulsion models.
        """
        return BundleLoader().get_factory_names(SERVICE_PROPULSION_WRAPPER)
