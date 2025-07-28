"""
Basis for registering and retrieving services
"""
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

import gc
import importlib
import logging
import re
from os import PathLike
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union

import pelix
from pelix.constants import BundleException
from pelix.framework import Bundle, BundleContext, Framework, FrameworkFactory
from pelix.internals.registry import ServiceReference
from pelix.ipopo.constants import SERVICE_IPOPO, use_ipopo
from pelix.ipopo.decorators import ComponentFactory, Property, Provides
from rich import box
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from .exceptions import (
    FastBundleLoaderDuplicateFactoryError,
    FastBundleLoaderUnknownFactoryNameError,
)
from .._utils.files import as_path
from .._utils.resource_management.contents import PackageReader

_CONSOLE = Console()
_LOGGER = logging.getLogger(__name__)
_LOGGER.propagate = False
_LOGGER.setLevel(logging.WARNING)

# Create RichHandler with custom formatter (only message)
_rich_handler = RichHandler(
    rich_tracebacks=True,
    markup=True,
    show_path=False,
    tracebacks_show_locals=False,
    show_time=False,
    show_level=False,
)
_formatter = logging.Formatter("%(message)s")  # no date, no level, no prefix
_rich_handler.setFormatter(_formatter)

# Attach handler only to this _LOGGER
_LOGGER.addHandler(_rich_handler)

"""Logger for this module"""

T = TypeVar("T")


class BundleLoader:
    """
    Helper class for loading Pelix bundles.
    """

    def __init__(self):
        """
        Constructor
        """
        self._framework = None

    @property
    def framework(self) -> Framework:
        """
        The currently running Pelix framework instance, or a new one if none is running (anyway,
        the framework instance will continue after deletion of this BundleLoader instance)
        """
        if FrameworkFactory.is_framework_running():
            self._framework = FrameworkFactory.get_framework()
            # Do not use self.context, because it will call back this.
            context = self._framework.get_bundle_context()
            if not context.get_service_reference(SERVICE_IPOPO):
                self._framework.install_bundle(SERVICE_IPOPO)
        else:
            self._framework = pelix.framework.create_framework(())
            self._framework.install_bundle(SERVICE_IPOPO)
            self._framework.start()
        return self._framework

    @property
    def context(self) -> BundleContext:
        """
        BundleContext instance of running Pelix framework
        """
        return self.framework.get_bundle_context()

    def explore_folder(
        self, folder_path: Union[str, PathLike], is_package: bool = False
    ) -> Tuple[Set[Bundle], Set[str]]:
        """
        Installs bundles found in *folder_path*.

        :param folder_path: The path of folder to scan
        :param is_package: if True, folder_path should be a Python package name that will be
                           scanned using importlib.resources
        :return: A 2-tuple, with the list of installed bundles
                 (:class:`~pelix.framework.Bundle`) and the list of the names
                 of the modules which import failed.
        """

        _LOGGER.info("Loading bundles from %s", folder_path)

        if is_package:
            bundles, failed = self._install_python_package(folder_path)
        else:
            bundles, unformatted_failed = self.framework.install_package(
                as_path(folder_path).as_posix(), True
            )
            # For some failure, the failed object can be returned as a set rather than a dict which
            # will prevent proper logging of the failures.
            failed = {}
            for failed_package in unformatted_failed:
                path_to_failed_package = (
                    as_path(folder_path).as_posix()
                    + "/"
                    + "/".join(failed_package.split(".")[1:])
                    + ".py"
                )
                failed[failed_package] = path_to_failed_package

        for bundle in bundles:
            _LOGGER.info(
                "Installed bundle %s (ID %s )", bundle.get_symbolic_name(), bundle.get_bundle_id()
            )
            bundle.start()
        if failed:
            self._log_failed_modules(failed)

        return bundles, failed

    def get_services(
        self, service_name: str, properties: dict = None, case_sensitive: bool = False
    ) -> Optional[list]:
        """
        Returns the services that match *service_name* and provided
        *properties* (if provided).

        :param service_name:
        :param properties:
        :param case_sensitive: if False, case of property values will be
                               ignored
        :return: the list of service instances
        """
        references = self._get_service_references(service_name, properties, case_sensitive)
        services = None
        if references is not None:
            services = [self.context.get_service(ref) for ref in references]

        return services

    def register_factory(
        self,
        component_class: Type[T],
        factory_name: str,
        service_names: Union[List[str], str],
        properties: dict = None,
    ) -> Type[T]:
        """
        Registers provided class as iPOPO component factory.

        :param component_class: the class of the components that will be provided by the factory
        :param factory_name: the name of the factory
        :param service_names: the service(s) that will be provided by the components
        :param properties: the properties associated to the factory
        :return: the input class, amended by iPOPO
        :raise FastDuplicateFactoryError:
        """

        obj = Provides(service_names)(component_class)
        with use_ipopo(self.context) as ipopo:
            if ipopo.is_registered_factory(factory_name):
                raise FastBundleLoaderDuplicateFactoryError(factory_name)

        if properties:
            for key, value in properties.items():
                obj = Property(field="_" + self._fieldify(key), name=key, value=value)(obj)

        factory = ComponentFactory(factory_name)(obj)

        return factory

    def get_factory_names(
        self, service_name: str = None, properties: dict = None, case_sensitive: bool = False
    ) -> List[str]:
        """
        Browses the available factory names to find what factories provide `service_name` (if
        provided) and match provided `properties` (if provided).

        if neither service_name nor properties are provided, all registered factory
        names are returned.

        :param service_name:
        :param properties:
        :param case_sensitive: if False, case of property values will be ignored
        :return: the list of factory names
        """
        with use_ipopo(self.context) as ipopo:
            all_names = ipopo.get_factories()
            if not service_name and not properties:
                return all_names

            names = []
            for name in all_names:
                details = ipopo.get_factory_details(name)
                to_be_kept = True
                if service_name and service_name not in details["services"][0]:
                    to_be_kept = False
                elif properties:
                    factory_properties: dict = details["properties"]
                    if case_sensitive:
                        to_be_kept = all(
                            item in factory_properties.items() for item in properties.items()
                        )
                    else:
                        for prop_name, prop_value in properties.items():
                            if prop_name not in factory_properties.keys():
                                to_be_kept = False
                                break
                            factory_prop_value = factory_properties[prop_name]
                            if isinstance(prop_value, str):
                                prop_value = prop_value.lower()
                                factory_prop_value = factory_prop_value.lower()
                            if prop_value != factory_prop_value:
                                to_be_kept = False
                                break
                if to_be_kept:
                    names.append(name)
        return names

    def get_factory_path(self, factory_name: str) -> str:
        """

        :param factory_name:
        :return: path of the file where the factory is defined
        """

        details = self.get_factory_details(factory_name)
        bundle: Bundle = details["bundle"]
        return bundle.get_location()

    def get_factory_properties(self, factory_name: str) -> dict:
        """
        :param factory_name:
        :return: properties of the factory
        """

        details = self.get_factory_details(factory_name)
        properties = details["properties"]
        return properties

    def get_factory_property(self, factory_name: str, property_name: str) -> Any:
        """
        :param factory_name:
        :param property_name:
        :return: property value, or None if property is not found
        """

        properties = self.get_factory_properties(factory_name)
        return properties.get(property_name)

    def get_factory_details(self, factory_name: str) -> Dict[str, Any]:
        """
        :param factory_name: name of the factory
        :return: factory details as in iPOPO
        :raise FastBundleLoaderUnknownFactoryNameError: unknown factory name
        """
        with use_ipopo(self.context) as ipopo:
            try:
                return ipopo.get_factory_details(factory_name)
            except ValueError as exc:
                raise FastBundleLoaderUnknownFactoryNameError(factory_name) from exc

    def get_instance_property(self, instance: Any, property_name: str) -> Any:
        """
        :param instance: any instance from :meth:~BundleLoader.instantiate_component
        :param property_name:
        :return: property value, or None if property is not found
        """

        try:
            return getattr(instance, "_" + self._fieldify(property_name))
        except AttributeError:
            return None

    def instantiate_component(self, factory_name: str, properties: dict = None) -> Any:
        """
        Instantiates a component from given factory

        :param factory_name: name of the factory
        :param properties: Initial properties of the component instance
        :return: the component instance
        :raise FastBundleLoaderUnknownFactoryNameError: unknown factory name
        """
        with use_ipopo(self.context) as ipopo:
            try:
                return ipopo.instantiate(
                    factory_name, self._get_instance_name(factory_name), properties
                )
            except TypeError as exc:
                raise FastBundleLoaderUnknownFactoryNameError(factory_name) from exc

    def clean_memory(self):
        """
        Removes all service objects from memory and runs garbage collector.
        """
        for bundle in self.context.get_bundles():
            # FIXME: it would be better to target bundles that provide FAST-OAD registration
            #        instead of just avoiding iPOPO bundles.
            if bundle.get_state() > Bundle.INSTALLED and "ipopo" not in bundle.get_symbolic_name():
                bundle.stop()
                bundle.start()
        gc.collect()

    def _get_instance_name(self, base_name: str):
        """
        Creates an instance name that is not currently used by iPOPO

        :param base_name: the beginning of the instance name
        :return: the created instance name
        """
        with use_ipopo(self.context) as ipopo:
            instances = ipopo.get_instances()
            instance_names = [i[0] for i in instances]
            i = 0
            name = "%s_%i" % (base_name, i)
            while name in instance_names:
                i = i + 1
                name = "%s_%i" % (base_name, i)

            return name

    def _get_service_references(
        self, service_name: str, properties: dict = None, case_sensitive: bool = False
    ) -> Optional[List[ServiceReference]]:
        """
        Returns the service references that match *service_name* and
        provided *properties* (if provided)

        :param service_name:
        :param properties:
        :param case_sensitive: if False, case of property values will be
                               ignored
        :return: a list of ServiceReference instances
        """

        # Dev Note: simple wrapper for BundleContext.get_all_service_references()

        if case_sensitive:
            operator = "="
        else:
            operator = "~="

        if not properties:
            ldap_filter = None
        else:
            ldap_filter = (
                "(&"
                + "".join(
                    [
                        "({0}{1}{2})".format(key, operator, value)
                        for key, value in properties.items()
                    ]
                )
                + ")"
            )
            _LOGGER.debug(ldap_filter)

        references = self.framework.find_service_references(service_name, ldap_filter)
        return references

    def _install_python_package(self, package_name: str) -> Tuple[Set[Bundle], dict[str, str]]:
        """
        Recursively loads indicated package and its submodules/subpackages.

        :param package_name: Name of the Python package or module to load
        :return: A 2-tuple:
            - Set of successfully installed Bundle objects
            - Dict of failed module names and their full paths
        """
        bundles = set()
        failed = {}  # dict {module_name: full_path}

        package = PackageReader(package_name)

        # Fallback root path used when importlib cannot locate the package filesystem path,
        # e.g., if the package is missing or in an unusual environment.
        root_package_path = "<unknown>"
        spec = importlib.util.find_spec(package_name)
        if spec and spec.origin:
            root_package_path = str(Path(spec.origin).parent)

        if package.has_error or not package.exists:
            failed[package_name] = root_package_path
            _LOGGER.warning("Failed to load package: %s", package_name)
            self._styled_rule(f"[bold red]ERROR: {package_name}[/bold red]")
            return bundles, failed  # Abort recursion early for broken package

        elif package.is_package:
            # It is a package, let's explore it.
            header_printed = False  # Ensure the error header is printed only once per package
            for item in package.contents:
                # Get the bundle name and path
                item_package = f"{package_name}.{item}"  # Qualified name
                item_path = f"{root_package_path}/{item}"  # Full path to the file or folder

                if "." in item:
                    # A file. Considered only if it is a Python file. Ignored otherwise.
                    if item.endswith(".py"):
                        try:
                            bundle = self.context.install_bundle(item_package[:-3])  # Remove .py
                            bundles.add(bundle)
                        except BundleException as e:
                            failed[item_package[:-3]] = item_path
                            if not header_printed:
                                _LOGGER.warning("Failed to load package: %s", package_name)
                                self._styled_rule(f"[bold red]ERROR: {package_name}[/bold red]")
                                header_printed = True
                            _LOGGER.warning("%s\nDetailed traceback:", e, exc_info=True)
                            self._styled_rule(first_newline=False)
                else:
                    # It's a subpackage. Recurse.
                    sub_bundles, sub_failed = self._install_python_package(item_package)
                    bundles.update(sub_bundles)
                    failed.update(sub_failed)

        return bundles, failed

    @staticmethod
    def _log_failed_modules(failed_modules: list[dict[str, str]]):
        table = Table(
            title="[bold red]FAST-OAD MODULE IMPORT FAILURE RECAP[/bold red]",
            show_header=True,
            header_style="bold red",
            box=box.HORIZONTALS,
            expand=True,
        )

        table.add_column("Failed Module", overflow="fold")
        table.add_column("Full path", overflow="fold")

        for module, path in failed_modules.items():
            table.add_row(module, path)

        # Let Rich render the table cleanly to terminal
        _CONSOLE.print()
        _CONSOLE.print(table)

    @staticmethod
    def _styled_rule(title: str = "", first_newline=True):
        if first_newline:
            _CONSOLE.print()
        _CONSOLE.rule(title, style="bright_black")
        _CONSOLE.print()

    @staticmethod
    def _fieldify(name: str) -> str:
        """
        Converts a string into a valid field name, i.e. replaces all spaces and
        non-word characters with an underscore.

        :param name: the string to fieldify
        :return: the field version of `name`
        """
        return re.compile(r"[\W_]+").sub("_", name).strip("_")
