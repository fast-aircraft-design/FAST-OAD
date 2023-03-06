"""Exceptions for module_management package."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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

from typing import List, Sequence

from fastoad.exceptions import FastError


class FastBundleLoaderDuplicateFactoryError(FastError):
    """
    Raised when trying to register a factory with an already used name.
    """

    def __init__(self, factory_name: str):
        """
        :param factory_name:
        """
        super().__init__('Name "%s" is already used.' % factory_name)
        self.factory_name = factory_name


class FastBundleLoaderUnknownFactoryNameError(FastError):
    """
    Raised when trying to instantiate a component from an unknown factory.
    """

    def __init__(self, factory_name: str):
        """
        :param factory_name:
        """
        super().__init__('"%s" is not registered.' % factory_name)
        self.factory_name = factory_name


class FastBadSystemOptionError(FastError):
    """
    Raised when some option name is not conform to OpenMDAO system definition.
    """

    def __init__(self, identifier, option_names):
        """
        :param identifier: system identifier
        :param option_names: incorrect option names
        """
        super().__init__(
            "OpenMDAO system %s does not accept following option(s): %s"
            % (identifier, option_names)
        )
        self.identifier = identifier
        self.option_names = option_names


class FastIncompatibleServiceClassError(FastError):
    """
    Raised when trying to register as service a class that does not implement
    the specified interface.
    """

    def __init__(self, registered_class: type, service_id: str, base_class: type):
        """
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


class FastNoSubmodelFoundError(FastError):
    """
    Raised when a submodel is required, but none has been declared.
    """

    def __init__(self, service_id: str):
        """
        :param service_id:
        """
        super().__init__('No submodel found for requirement "%s"' % service_id)
        self.service_id = service_id


class FastTooManySubmodelsError(FastError):
    """
    Raised when several candidates are declared for a required submodel, but
    none has been selected.
    """

    def __init__(self, service_id: str, candidates: Sequence[str]):
        """
        :param service_id:
        :param candidates:
        """
        super().__init__(
            'Submodel requirement "%s" needs a choice among following candidates: %s'
            % (service_id, candidates)
        )
        self.service_id = service_id
        self.candidates = candidates


class FastUnknownSubmodelError(FastError):
    """
    Raised when a submodel identifier is unknown for given required service.
    """

    def __init__(self, service_id: str, submodel_id: str, submodel_ids: List[str]):
        """
        :param service_id:
        :param submodel_id:
        :param submodel_ids:
        """

        msg = '"%s" is not a submodel identifier for requirement "%s"' % (submodel_id, service_id)
        msg += "\nValid identifiers are %s" % submodel_ids
        super().__init__(msg)
        self.service_id = service_id
        self.submodel_id = submodel_id


class FastNoDistPluginError(FastError):
    """Raised when no installed package with FAST-OAD plugin is available."""

    def __init__(self):
        super().__init__("This feature needs plugins, but no plugin available.")


class FastUnknownDistPluginError(FastError):
    """Raised when a distribution name is not found among distribution with FAST-OAD plugins."""

    def __init__(self, dist_name):
        self.dist_name = dist_name
        super().__init__(
            f'No installed package with FAST-OAD plugin found with name "{dist_name}".'
        )


class FastSeveralDistPluginsError(FastError):
    """
    Raised when no distribution name has been specified but several distribution
    with FAST-OAD plugins are available.
    """

    def __init__(self):
        super().__init__(
            "Several installed packages with FAST-OAD plugins are available. "
            "One must be specified."
        )


class FastNoAvailableConfigurationFileError(FastError):
    """Raised when a configuration file is asked, but none is available in plugins."""

    def __init__(self):
        super().__init__("No configuration file provided with currently installed plugins.")


class FastUnknownConfigurationFileError(FastError):
    """Raised when a configuration file is not found for named distribution."""

    def __init__(self, configuration_file, dist_name):
        self.configuration_file = configuration_file
        self.dist_name = dist_name
        super().__init__(
            f'Configuration file "{configuration_file}" not provided with '
            f'installed package "{dist_name}".'
        )


class FastSeveralConfigurationFilesError(FastError):
    """
    Raised when no configuration file has been specified but several configuration files are
    provided with the distribution."""

    def __init__(self, dist_name):
        self.dist_name = dist_name
        super().__init__(
            f'Installed package "{dist_name}" provides several configuration files. '
            "One must be specified."
        )


class FastNoAvailableSourceDataFileError(FastError):
    """Raised when a source data file is requested, but none is available in plugins."""

    def __init__(self):
        super().__init__("No source data file provided with currently installed plugins.")


class FastUnknownSourceDataFileError(FastError):
    """Raised when a source data file is not found for named distribution."""

    def __init__(self, source_data_file, dist_name):
        self.source_data_file = source_data_file
        self.dist_name = dist_name
        super().__init__(
            f'Source data file "{source_data_file}" not provided with '
            f'installed package "{dist_name}".'
        )


class FastSeveralSourceDataFilesError(FastError):
    """
    Raised when no source data file has been specified but several source data files are
    provided with the distribution."""

    def __init__(self, dist_name):
        self.dist_name = dist_name
        super().__init__(
            f'Installed package "{dist_name}" provides several source data files. '
            "One must be specified."
        )
