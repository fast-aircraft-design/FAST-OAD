"""Module for managing sub-models registration and usage"""
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

from typing import Dict, TypeVar

from .exceptions import (
    FastNoSubmodelFoundError,
    FastTooManySubmodelsError,
    FastUnknownSubmodelError,
)
from .service_registry import RegisterOpenMDAOService

T = TypeVar("T")


class RegisterSubmodel(RegisterOpenMDAOService):
    """
    Decorator class that allows to register services and associated providers.

    Then basic registering of a class is done with::

        @RegisterSubmodel("my.service", "id.of.the.provider")
        class MyService:
            ...
    """

    active_models: Dict[str, str] = {}

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

        instance = super().get_system(submodel_id, options)

        return instance
