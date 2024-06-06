"""Module for registering services."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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


from os import PathLike
from types import MethodType
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import openmdao.api as om
from openmdao.core.system import System

from ._plugins import FastoadLoader
from .constants import (
    DESCRIPTION_PROPERTY_NAME,
    DOMAIN_PROPERTY_NAME,
    ModelDomain,
    OPTION_PROPERTY_NAME,
    SERVICE_OPENMDAO_SYSTEM,
    SERVICE_PROPULSION_WRAPPER,
)
from .exceptions import (
    FastBadSystemOptionError,
    FastIncompatibleServiceClassError,
    FastNoSubmodelFoundError,
    FastTooManySubmodelsError,
    FastUnknownSubmodelError,
)
from ..model_base.propulsion import IOMPropulsionWrapper
from ..openmdao.variables import Variable

T = TypeVar("T")


class RegisterService:
    """
    Decorator class that allows to register services and associated providers.

    This class also provides class methods for getting service providers and
    information about them.

    The basic registering of a class is done with::

        @RegisterService("my.service.id", "id.of.the.provider")
        class MyService:
            ...

    A child of this class may define a particular base class or interface
    that should be parent to all registered service providers.

    The definition of the base class is done when subclassing, e.g.::

        class RegisterSomeService( RegisterService, base_class=ISomeService):
            "Allows to register classes that implement interface ISomeService."
    """

    @classmethod
    def __init_subclass__(cls, *, base_class: type = object):
        """

        :param base_class: the base class that shall be parent to all registered classes
        """

        cls._base_class = base_class

    def __init__(self, service_id: str, provider_id: str, desc=None):
        """
        :param service_id: the identifier of the provided service
        :param provider_id: the identifier of the service provider to register
        :param desc: description of the service provider. If not provided, the docstring
                     of decorated class will be used.
        """
        self._service_id = service_id
        self._id = provider_id
        self._desc = desc

    def __call__(self, service_class: Type[T]) -> Type[T]:
        if not issubclass(service_class, self._base_class):
            raise FastIncompatibleServiceClassError(
                service_class, self._service_id, self._base_class
            )

        return FastoadLoader().register_factory(
            service_class, self._id, self._service_id, self.get_properties(service_class)
        )

    def get_properties(self, service_class: Type[T]) -> dict:
        """
        Override this method to modify the properties that will be associated to
        the registered service provider.

        This basic version ensures the associated description property is the one
        provided when instantiating this decorator class, if it is provided. Otherwise,
        it will be the docstring of the decorated class.

        :param service_class: the class that will be registered as service provider
        :return: the dictionary of properties that will be associated to the registered
                 service provider
        """
        return {DESCRIPTION_PROPERTY_NAME: self._desc if self._desc else service_class.__doc__}

    @classmethod
    def explore_folder(cls, folder_path: str):
        """
        Explores provided folder and looks for service providers to register.

        :param folder_path:
        """
        FastoadLoader().explore_folder(folder_path)

    @classmethod
    def get_provider_ids(cls, service_id: str) -> List[str]:
        """
        :param service_id:
        :return: the list of identifiers of providers of the service.
        """
        return FastoadLoader().get_factory_names(service_id)

    @classmethod
    def get_provider(cls, service_provider_id: str, options: dict = None) -> Any:
        """
        Instantiates the desired service provider.

        :param service_provider_id: identifier of a registered service provider
        :param options: options that should be associated to the created instance
        :return: the created instance
        """

        properties = FastoadLoader().get_factory_properties(service_provider_id).copy()

        if options:
            properties[OPTION_PROPERTY_NAME] = properties[OPTION_PROPERTY_NAME].copy()
            properties[OPTION_PROPERTY_NAME].update(options)

        return FastoadLoader().instantiate_component(service_provider_id, properties)

    @classmethod
    def get_provider_description(cls, instance_or_id: Union[str, T]) -> str:
        """
        :param instance_or_id: an identifier or an instance of a registered service provider
        :return: the description associated to given instance or identifier
        """

        return cls._get_provider_property(instance_or_id, DESCRIPTION_PROPERTY_NAME)

    @classmethod
    def get_provider_domain(cls, instance_or_id: Union[str, System]) -> ModelDomain:
        """
        :param instance_or_id: an identifier or an instance of a registered service provider
        :return: the model domain associated to given instance or identifier
        """
        return cls._get_provider_property(instance_or_id, DOMAIN_PROPERTY_NAME)

    @classmethod
    def _get_provider_property(cls, instance_or_id: Any, property_name: str) -> Any:
        """
        :param instance_or_id: an identifier or an instance of a registered service provider
        :param property_name:
        :return: the property value associated to given instance or identifier
        """

        if isinstance(instance_or_id, str):
            return FastoadLoader().get_factory_property(instance_or_id, property_name)

        return FastoadLoader().get_instance_property(instance_or_id, property_name)


class _RegisterOpenMDAOService(RegisterService, base_class=System):
    """
    Base class for registering OpenMDAO systems.

    This class ensures that variable_descriptions.txt files that are at the
    same package level as the decorated class are loaded.

    It also ensures that, when the OpenMDAO system is instantiated, its options
    are fed with provided values, that can be provided when instantiating this class,
    or when instantiating the system with :class:`get_system`.
    """

    def __init__(self, service_id: str, provider_id: str, desc=None, options: dict = None):
        """
        :param service_id: the identifier of the provided service
        :param provider_id: the identifier of the service provider to register
        :param desc: description of the service. If not provided, the docstring will be used.
        :param options: a dictionary of options that will be defaults when instantiating the system
        """
        super().__init__(service_id, provider_id, desc)
        self._options = options

    def get_properties(self, service_class: Type[T]) -> dict:
        properties = super().get_properties(service_class)
        properties.update({OPTION_PROPERTY_NAME: self._options if self._options else {}})
        return properties

    def __call__(self, service_class: Type[T]) -> Type[T]:

        # service_class.__module__ provides the name for the .py file, but
        # we want just the parent package name.
        package_name = ".".join(service_class.__module__.split(".")[:-1])

        Variable.read_variable_descriptions(package_name)

        # and now the actual call
        return super().__call__(service_class)

    @classmethod
    def explore_folder(cls, folder_path: Union[str, PathLike]):
        """
        Explores provided folder and looks for service providers to register.

        :param folder_path:
        """
        Variable.read_variable_descriptions(folder_path)
        super().explore_folder(folder_path)

    @classmethod
    def get_system(cls, identifier: str, options: dict = None) -> System:
        """
        Specialized version of :meth:`RegisterSpecializedService.get_provider` that allows to
        define OpenMDAO options on-the-fly.

        :param identifier: identifier of the registered class
        :param options: option values at system instantiation
        :return: an OpenMDAO system instantiated from the registered class
        """

        system = super().get_provider(identifier, options)

        # Before making the system available to get options from OPTION_PROPERTY_NAME,
        # check that options are valid to avoid failure at setup()
        options = getattr(system, "_" + OPTION_PROPERTY_NAME, None)
        if options:
            invalid_options = [name for name in options if name not in system.options]
            if invalid_options:
                raise FastBadSystemOptionError(identifier, invalid_options)

        decorated_system = cls._option_decorator(system)
        return decorated_system

    @staticmethod
    def _option_decorator(instance: System) -> System:
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
        #   is to rename the original `setup()` as `_setup_before_option_decorator()`, and create a
        #   new `setup()` that does its job and then calls `_setup_before_option_decorator()`.

        def setup(self):
            """Will replace the original setup() method"""

            # Use values from iPOPO option properties
            option_dict = getattr(self, "_" + OPTION_PROPERTY_NAME, None)
            if option_dict:
                for name, value in option_dict.items():
                    self.options[name] = value

            # Call the original setup method
            self._setup_before_option_decorator()

        # Move the (already bound) method "setup" to "_setup_before_option_decorator"
        setattr(instance, "_setup_before_option_decorator", instance.setup)

        # Create and bind the new "setup" method
        setup_method = MethodType(setup, instance)
        setattr(instance, "setup", setup_method)

        return instance


class RegisterSpecializedService(RegisterService):
    """
    Base class for decorator classes that allow to register a particular service.

    The service may be associated to a base class (or interface). The registered class must
    inherit from this base class.

    Unlike :class:`RegisterService`, this class has to be subclassed, because the service
    identifier is defined when subclassing.

    The definition of the base class is done by subclassing, e.g.::

        class RegisterSomeService( RegisterSpecializedService,
                                   base_class=ISomeService,
                                   service_id="my.particularservice"):
            "Allows to register classes that implement interface ISomeService."


    Then basic registering of a class is done with::

        @RegisterSomeService("my.particularservice.provider")
        class ParticularService(ISomeService):
            ...
    """

    _base_class: type
    service_id: str

    @classmethod
    def __init_subclass__(
        cls, *, base_class: type = object, service_id: str = None, domain: ModelDomain = None
    ):
        """

        :param base_class: the base class that shall be parent to all registered classes
        :param service_id: the identifier of the service. If not provided, it will be automatically
                           set.
        :param domain: a category that can be associated to the registered service
        """

        super(RegisterSpecializedService, cls).__init_subclass__(base_class=base_class)

        if service_id:
            cls.service_id = service_id
        else:
            cls.service_id = "%s.%s" % (__name__, cls.__name__)

        cls._domain = domain

    def __init__(
        self, provider_id: str, desc=None, domain: ModelDomain = None, options: dict = None
    ):
        """
        :param provider_id: the identifier of the service provider to register
        :param desc: description of the service. If not provided, the docstring will be used.
        :param domain: a category for the registered service provider
        :param options: a dictionary of options that can be associated to the service provider
        """
        super().__init__(self.__class__.service_id, provider_id, desc)
        self._options = options
        if domain:
            self._domain = domain

    def get_properties(self, service_class: Type[T]) -> dict:
        properties = super().get_properties(service_class)
        properties.update(
            {
                DOMAIN_PROPERTY_NAME: self._domain if self._domain else ModelDomain.UNSPECIFIED,
                OPTION_PROPERTY_NAME: self._options if self._options else {},
            }
        )
        return properties

    @classmethod
    def get_provider_ids(cls) -> List[str]:
        """
        :return: the list of identifiers of providers of the service.
        """
        return super().get_provider_ids(cls.service_id)


class _RegisterSpecializedOpenMDAOService(RegisterSpecializedService, _RegisterOpenMDAOService):
    """
    Base class for specialized decorator classes for registering OpenMDAO systems.

    This class ensures that:

      - variable_descriptions.txt files that are at the same package level as the decorated class
        are loaded.
      - OpenMDAO options can be provided (see :class:`RegisterOpenMDAOService` for details)
    """


class RegisterPropulsion(
    _RegisterSpecializedOpenMDAOService,
    base_class=IOMPropulsionWrapper,
    service_id=SERVICE_PROPULSION_WRAPPER,
    domain=ModelDomain.PROPULSION,
):
    """
    Decorator class for registering an OpenMDAO wrapper of a propulsion-dedicated model.
    """


class RegisterOpenMDAOSystem(
    _RegisterSpecializedOpenMDAOService, base_class=System, service_id=SERVICE_OPENMDAO_SYSTEM
):
    """
    Decorator class for registering an OpenMDAO system for use in FAST-OAD configuration.

    If a variable_descriptions.txt file is in the same folder as the class module, its
    content is loaded (once, even if several classes are registered at the same level).
    """


class RegisterSubmodel(_RegisterOpenMDAOService):
    """
    Decorator class that allows to submodels.

    Submodels are OpenMDAO systems that fulfill a requirement (service id) in a FAST-OAD module.

    :attr:`active_models` defines the submodel to be used for any service identifier
    it has as key. See :meth:`get_submodel` for more details.

    The registering of a class is done with::

        @RegisterSubmodel("my.service", "id.of.the.provider")
        class MyService:
            ...

    Then the submodel can be instantiated and used with::

        submodel_instance = RegisterSubmodel.get_submodel("my.service")
        some_model.add_subsystem("my_submodel", submodel_instance, promotes=["*"])
        ...
    """

    #: Dictionary (key = service id, value=provider id) that defines submodels to
    #: be used for associated services.
    active_models: Dict[str, Optional[str]] = {}

    @classmethod
    def get_submodel(cls, service_id: str, options: dict = None):
        """
        Provides a submodel for the given service identifier.

        If :attr:`active_models` has `service_id` as key:
            - if the associated value is a non-empty string, a submodel will be instantiated with
              this string as submodel identifier. If the submodel identifier matches nothing, an
              error will be raised.
            - if the associated value is None, an empty submodel (om.Group()) will be instantiated.
              You may see it as a way to deactivate a particular submodel.

        If :attr:`active_models` has `service_id` has NOT as key:
            - if no submodel is declared for this `service_id`, an error will be raised.
            - if one and only one submodel is declared for this `service_id`, it will be
              instantiated.
            - if several submodels are declared for this `service_id`, an error will be raised.

        If an actual (not empty) submodel is defined, provided options will be used.

        :param service_id:
        :param options:
        :return: the instantiated submodel
        """
        submodel_ids = FastoadLoader().get_factory_names(service_id)

        if service_id in cls.active_models:
            submodel_id = cls.active_models[service_id]
            if submodel_id and submodel_id not in submodel_ids:
                raise FastUnknownSubmodelError(service_id, submodel_id, submodel_ids)
        else:
            if len(submodel_ids) == 0:
                raise FastNoSubmodelFoundError(service_id)
            if len(submodel_ids) > 1:
                raise FastTooManySubmodelsError(service_id, submodel_ids)

            submodel_id = submodel_ids[0]

        if submodel_id:
            instance = super().get_system(submodel_id, options)
        else:
            instance = om.Group()

        return instance

    @classmethod
    def cancel_submodel_deactivations(cls):
        """Reactivates all submodels that have been deactivated."""
        deactivated_submodel_ids = [k for k, v in cls.active_models.items() if not v]
        for submodel_id in deactivated_submodel_ids:
            del cls.active_models[submodel_id]
