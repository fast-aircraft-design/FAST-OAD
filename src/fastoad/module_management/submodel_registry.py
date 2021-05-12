"""Module for managing sub-models registration and usage"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

from typing import Dict, Type, TypeVar

from ._bundle_loader import BundleLoader
from .constants import (
    DESCRIPTION_PROPERTY_NAME,
    DOMAIN_PROPERTY_NAME,
    ModelDomain,
    OPTION_PROPERTY_NAME,
)
from .exceptions import (
    FastNoSubmodelFoundError,
    FastTooManySubmodelsError,
    FastUnknownSubmodelError,
)

T = TypeVar("T")


class RegisterSubmodel:
    """
    Decorator class that allows to register services and associated providers.

    Then basic registering of a class is done with::

        @RegisterSubmodel("my.service", "id.of.the.provider")
        class MyService:
            ...
    """

    active_models: Dict[str, str] = {}
    _loader = BundleLoader()

    def __init__(self, service_id: str, provider_id: str, desc=None, domain: ModelDomain = None):
        """
        :param service_id: the identifier of the provided service
        :param provider_id: the identifier of the service provider to register
        :param desc: description of the service. If not provided, the docstring
                     of decorated class will be used.
        :param domain: a category for the registered service provider
        """
        self._service_id = service_id
        self._id = provider_id
        self._desc = desc
        self._domain = None
        self._domain = domain

    def __call__(self, service_class: Type[T]) -> Type[T]:
        properties = {
            DOMAIN_PROPERTY_NAME: self._domain if self._domain else ModelDomain.UNSPECIFIED,
            DESCRIPTION_PROPERTY_NAME: self._desc if self._desc else service_class.__doc__,
        }

        return self._loader.register_factory(service_class, self._id, self._service_id, properties)

    @classmethod
    def get_submodel(cls, service_id: str, options: dict = None):
        """

        :param service_id:
        :param options:
        :return:
        """
        submodel_ids = cls._loader.get_factory_names(service_id)

        if service_id in cls.active_models and cls.active_models[service_id]:
            submodel_id = cls.active_models[service_id]
            if submodel_id not in submodel_ids:
                raise FastUnknownSubmodelError(service_id, submodel_id, submodel_ids)
        else:
            if len(submodel_ids) == 0:
                raise FastNoSubmodelFoundError(service_id)
            if len(submodel_ids) > 1:
                raise FastTooManySubmodelsError(service_id, submodel_ids)

            submodel_id = submodel_ids[0]

        properties = {
            OPTION_PROPERTY_NAME: options if options else {},
        }

        instance = cls._loader.instantiate_component(submodel_id, properties)

        return instance
