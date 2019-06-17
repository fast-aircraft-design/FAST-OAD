# -*- coding: utf-8 -*-
"""
Basis for registering and retrieving services
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
from typing import List, Tuple, Set, Union, Optional

import pelix
from pelix.framework import FrameworkFactory, Framework, Bundle, BundleContext
from pelix.internals.registry import ServiceReference
from pelix.ipopo.constants import SERVICE_IPOPO

_LOGGER = logging.getLogger(__name__)
"""Logger for this module"""


class BundleLoader:
    """
    Helper class for loading Pelix bundles.
    """

    def __init__(self):
        """
        Constructor
        """
        self.__framework: Framework = None

    @property
    def framework(self) -> Framework:
        """
        Returns the Pelix framework instance. If None is running, a new one
        will be started and initialized. The framework will continue after
        deletion of this BundleLoader instance and will be reused by next instances.

        :return: Pelix framework instance
        """
        if FrameworkFactory.is_framework_running():
            self.__framework = FrameworkFactory.get_framework()
            # Do not use self.context, because it will call back this.
            context = self.__framework.get_bundle_context()
            if not context.get_service_reference(SERVICE_IPOPO):
                self.__framework.install_bundle(SERVICE_IPOPO)
        else:
            self.__framework = pelix.framework.create_framework(())
            self.__framework.install_bundle(SERVICE_IPOPO)
            self.__framework.start()
        return self.__framework

    @property
    def context(self) -> BundleContext:
        """
        :return: BundleContext instance of runnning Pelix framework
        """
        return self.framework.get_bundle_context()

    def install_packages(self, folder_path: str) \
            -> Tuple[Set[Bundle], Set[Union[str, bytes, int, None]]]:
        """
        Installs and starts bundles found in *folder_path*.

        :param folder_path: The path of folder to scan
        :return: A 2-tuple, with the list of installed bundles
                 (:class:`~pelix.framework.Bundle`) and the list of the names
                 of the modules which import failed.
        :raise ValueError: Invalid path
        """

        _LOGGER.info('Loading bundles from %s', folder_path)
        bundles, failed = self.context.install_package(folder_path, True)

        for bundle in bundles:
            _LOGGER.info('Installed bundle %s (ID %s )'
                         , bundle.get_symbolic_name(), bundle.get_bundle_id())
            bundle.start()
        for _f in failed:
            _LOGGER.warning('Failed to import module %s', _f)

        return bundles, failed

    def get_service(self, service_name: str) -> Optional[object]:
        """
        Returns the service that match *service_name*.

        If there are more than one service that mach *service_name*, only the first one is
        returned.

        If several services are expected, please use :meth:`get_services` instead.

        :param service_name:
        :return: the service instance, or None if not found
        """
        services = self.get_services(service_name)
        if services is not None:
            if len(services) > 1:
                _LOGGER.warning('More than one service found for spec %s', service_name)
            return services[0]

        return None

    def get_services(self
                     , service_name: str
                     , properties: dict = None
                     , case_sensitive: bool = False) \
            -> Optional[list]:
        """
        Returns the services that match *service_name* and provided
        *properties* (if provided).

        In order to have access to service
        metadata such a properties, please use
        :meth:`get_service_references` instead.

        :param service_name:
        :param properties:
        :param case_sensitive: if False, case of property values will be
        ignored
        :return: the list of service instances
        """
        references = self.get_service_references(service_name, properties
                                                 , case_sensitive)
        services = None
        if references is not None:
            services = [self.context.get_service(ref) for ref in references]
        return services

    def get_service_references(self
                               , service_name: str
                               , properties: dict = None
                               , case_sensitive: bool = False) \
            -> Optional[List[ServiceReference]]:
        """
        Returns the service references that match *service_name* and
        provided *properties* (if provided)

        :param service_name:
        :param properties:
        :param case_sensitive: if False, case of property values will be
        ignored
        :return: a list of ServiceReference instances
        """

        # Dev Note: simple wrapper for
        # BundleContext.get_all_service_references()

        if case_sensitive:
            operator = '='
        else:
            operator = '~='

        if not properties:
            ldap_filter = None
        else:
            ldap_filter = '(&' + ''.join(
                ['({0}{1}{2})'.format(key, operator, value)
                 for key, value in properties.items()]) + ')'
            _LOGGER.debug(ldap_filter)

        references = self.context.get_all_service_references(service_name
                                                             , ldap_filter)
        return references
