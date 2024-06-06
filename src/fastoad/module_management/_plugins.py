"""
Plugin system for declaration of FAST-OAD models.
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


# We need __future__ to allow using DistributionNameDict as annotation in FastoadLoader
# Otherwise, in Python 3.8, we get "TypeError: 'ABCMeta' object is not subscriptable"
from __future__ import annotations

import logging
import sys
import warnings
from dataclasses import InitVar, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional

import numpy as np

from fastoad.openmdao.variables import Variable
from ._bundle_loader import BundleLoader
from .exceptions import (
    FastNoAvailableConfigurationFileError,
    FastNoAvailableSourceDataFileError,
    FastNoDistPluginError,
    FastSeveralConfigurationFilesError,
    FastSeveralDistPluginsError,
    FastSeveralSourceDataFilesError,
    FastUnknownConfigurationFileError,
    FastUnknownDistPluginError,
    FastUnknownSourceDataFileError,
)
from .._utils.dicts import AbstractNormalizedDict
from .._utils.resource_management.contents import PackageReader

if sys.version_info >= (3, 10):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata

_LOGGER = logging.getLogger(__name__)  # Logger for this module

OLD_MODEL_PLUGIN_ID = "fastoad_model"
MODEL_PLUGIN_ID = "fastoad.plugins"


class DistributionNameDict(AbstractNormalizedDict):
    """
    Dictionary where keys are distribution names.

    As per PEP 426, "all comparisons of distribution names MUST be case-insensitive, and MUST
    consider hyphens and underscores to be equivalent."
    This equivalence is implemented by forcing keys to be lower case with only hyphens.
    """

    @staticmethod
    def normalize(dist_name: Optional[str]):  # pylint: disable=arguments-differ
        """
        Returns a normalized distribution name for PEP-426-compliant comparison of distribution
        names.

        :param dist_name:
        :return: dist_name in lower case with hyphens ("-") instead of underscores ("_")
        """
        if dist_name:
            return dist_name.lower().replace("_", "-")
        return dist_name


class SubPackageNames(Enum):
    """Enumeration of possible plugin subpackages."""

    MODELS = "models"
    NOTEBOOKS = "notebooks"
    CONFIGURATIONS = "configurations"
    SOURCE_DATA_FILES = "source_data_files"


@dataclass
class ResourceInfo:
    """
    Class for storing information about configuration and source data files provided by plugins.
    """

    name: str
    dist_name: str
    plugin_name: str
    package_name: str


@dataclass
class PluginDefinition:
    """
    Stores and provides FAST-OAD plugin data.
    """

    dist_name: str
    plugin_name: str
    package_name: str = ""
    subpackages: Dict[SubPackageNames, str] = field(default_factory=dict)

    def detect_subfolders(self):
        """
        Scans plugin folders and populates :attr:`subpackages`.
        """
        package = PackageReader(self.package_name)
        for subpackage_name in SubPackageNames:
            if subpackage_name.value in package.contents:
                self.subpackages[subpackage_name] = ".".join(
                    [self.package_name, subpackage_name.value]
                )

    def get_configuration_file_list(self) -> List[ResourceInfo]:
        """
        :return: List of configuration files that are provided by the distribution.
        """
        if SubPackageNames.CONFIGURATIONS in self.subpackages:
            return [
                ResourceInfo(
                    name=file,
                    dist_name=self.dist_name,
                    plugin_name=self.plugin_name,
                    package_name=self.subpackages[SubPackageNames.CONFIGURATIONS],
                )
                for file in PackageReader(self.subpackages[SubPackageNames.CONFIGURATIONS]).contents
                if Path(file).suffix in [".yml", ".yaml"]
            ]

        return []

    def get_source_data_file_list(self) -> List[ResourceInfo]:
        """
        :return: List of data files that are provided by the distribution.
        """
        if SubPackageNames.SOURCE_DATA_FILES in self.subpackages:
            return [
                ResourceInfo(
                    name=file,
                    dist_name=self.dist_name,
                    plugin_name=self.plugin_name,
                    package_name=self.subpackages[SubPackageNames.SOURCE_DATA_FILES],
                )
                for file in PackageReader(
                    self.subpackages[SubPackageNames.SOURCE_DATA_FILES]
                ).contents
                if Path(file).suffix in [".xml"]
            ]

        return []


@dataclass
class DistributionPluginDefinition(dict):
    """
    Stores and provides data for FAST-OAD plugins provided by a Python distribution.
    """

    dist_name: InitVar[str] = None

    def __post_init__(self, dist_name):
        self._dist_name = dist_name

    @property
    def dist_name(self):
        """Name of the distribution that contains the defined plugin."""
        return self._dist_name

    @dist_name.setter
    def dist_name(self, dist_name):
        self._dist_name = DistributionNameDict.normalize(dist_name)

    def read_entry_point(self, entry_point: importlib_metadata.EntryPoint, group: str):
        """
        Adds plugin definition from provided entry point to

        Does nothing if entry_point.dist.project_name is not equal to :attr:`dist_name`

        :param entry_point:
        :param group:
        """
        if self.dist_name != DistributionNameDict.normalize(entry_point.dist.name):
            return

        plugin_definition = PluginDefinition(
            dist_name=self.dist_name,
            plugin_name=entry_point.name,
        )
        plugin_definition.package_name = entry_point.module
        self[entry_point.name] = plugin_definition

        if group == OLD_MODEL_PLUGIN_ID:
            warnings.warn(
                f'"{self.dist_name}" package uses `fastoad_model` as plugin group ID, which is '
                "deprecated. `fastoad.plugins` should be used instead.",
                DeprecationWarning,
            )
            self[entry_point.name].subpackages[SubPackageNames.MODELS] = entry_point.module

        if group == MODEL_PLUGIN_ID:
            self[entry_point.name].detect_subfolders()

    def get_source_data_file_list(self, plugin_name=None) -> List[ResourceInfo]:
        """
        :param plugin_name: If provided, only file names provided by the plugin in
                            the distribution will be returned, or an empty list if
                            the plugin is not in the distribution.
        :return:  List of source data file information that are provided by the distribution.
        """
        file_list = []
        if plugin_name:
            if plugin_name in self:
                file_list = self[plugin_name].get_source_data_file_list()
        else:
            for plugin in self.values():
                file_list += plugin.get_source_data_file_list()

        return file_list

    def get_source_data_file_info(self, file_name=None, plugin_name=None) -> ResourceInfo:
        """
        :param file_name: can be None if only one configuration file is provided in the
                          distribution (or in the plugin if `plugin_name` is provided)
        :param plugin_name:
        :return: information for specified configuration file name.
        :raise FastSeveralSourceDataFilesError: if several source data files are available but
                                               `file_name` has not been provided.
        :raise FastUnknownSourceDataFileError: if the specified source data file is not available.
        :raise FastNoAvailableSourceDataFileError: if there a no source data file in the plugin.
        """

        source_data_file_list = self.get_source_data_file_list(plugin_name)
        if not source_data_file_list:
            raise FastNoAvailableSourceDataFileError()

        if file_name is None:
            if len(source_data_file_list) > 1:
                raise FastSeveralSourceDataFilesError(self.dist_name)
            file_info = source_data_file_list[0]
        else:
            matching_list = list(filter(lambda item: item.name == file_name, source_data_file_list))
            if len(matching_list) == 0:
                raise FastUnknownSourceDataFileError(file_name, self.dist_name)

            # Here we implicitly assume that plugin developers will ensure that there will be
            # no duplicates in conf file names (possible if several plugins are in the
            # same installed package, but such practice is discouraged).
            file_info = matching_list[0]

        return file_info

    def get_configuration_file_list(self, plugin_name=None) -> List[ResourceInfo]:
        """
        :param plugin_name: If provided, only file names provided by the plugin in
                            the distribution will be returned, or an empty list if
                            the plugin is not in the distribution.
        :return:  List of configuration file information that are provided by the distribution.
        """
        file_list = []
        if plugin_name:
            if plugin_name in self:
                file_list = self[plugin_name].get_configuration_file_list()
        else:
            for plugin in self.values():
                file_list += plugin.get_configuration_file_list()

        return file_list

    def get_configuration_file_info(self, file_name=None, plugin_name=None) -> ResourceInfo:
        """
        :param file_name: can be None if only one configuration file is provided in the
                          distribution (or in the plugin if `plugin_name` is provided)
        :param plugin_name:
        :return: information for specified configuration file name.
        :raise FastSeveralConfigurationFilesError: if several configuration files are available
                                                   but `file_name` has not been provided.
        :raise FastUnknownConfigurationFileError: if the specified configuration file is not
                                                  available.
        """
        conf_file_list = self.get_configuration_file_list(plugin_name)
        if not conf_file_list:
            raise FastNoAvailableConfigurationFileError()

        if file_name is None:
            if len(conf_file_list) > 1:
                raise FastSeveralConfigurationFilesError(self.dist_name)
            file_info = conf_file_list[0]
        else:
            matching_list = list(filter(lambda item: item.name == file_name, conf_file_list))
            if len(matching_list) == 0:
                raise FastUnknownConfigurationFileError(file_name, self.dist_name)

            # Here we implicitly assume that plugin developers will ensure that there will be
            # no duplicates in conf file names (possible if several plugins are in the
            # same installed package, but such practice is discouraged).
            file_info = matching_list[0]

        return file_info

    def get_notebook_folder_list(self, plugin_name=None) -> List[ResourceInfo]:
        """
        :param plugin_name: If provided, only notebook folder provided by the plugin (if any)
                            will be returned, or an empty list if the plugin is not in the
                            distribution.
        :return:  List of notebook folder information that are provided by the distribution.
        """
        if plugin_name:
            plugin_names = [plugin_name] if plugin_name in self else []
        else:
            plugin_names = self.keys()

        info = []
        for name in plugin_names:
            plugin_def = self[name]
            if SubPackageNames.NOTEBOOKS in plugin_def.subpackages:
                info.append(
                    ResourceInfo(
                        name=SubPackageNames.NOTEBOOKS.value,
                        dist_name=self.dist_name,
                        plugin_name=name,
                        package_name=plugin_def.subpackages[SubPackageNames.NOTEBOOKS],
                    )
                )
        return info

    def to_dict(self) -> Dict:
        """
        :return: a dict that contains plugin information
        """
        has_models = np.any(
            [SubPackageNames.MODELS in definition.subpackages for definition in self.values()]
        )
        has_notebooks = np.any(
            [SubPackageNames.NOTEBOOKS in definition.subpackages for definition in self.values()]
        )
        conf_files = [item.name for item in self.get_configuration_file_list()]
        source_data_files = [item.name for item in self.get_source_data_file_list()]
        return dict(
            installed_package=self.dist_name,
            has_models=has_models,
            has_notebooks=has_notebooks,
            configurations=sorted(conf_files),
            source_data_files=sorted(source_data_files),
        )


class FastoadLoader(BundleLoader):
    """
    Specialized :class:`BundleLoader` that will load plugins at first instantiation.

    It also provides data from available plugins.
    """

    # This class attribute is private and is accessed through a property to ensure
    # that the class has been instantiated before the attribute is used.
    _dist_plugin_definitions: DistributionNameDict[str, DistributionPluginDefinition]

    _loaded = False

    def __init__(self):
        super().__init__()
        if not self.__class__._loaded:
            # Setting cls.loaded to True already ensures that a second instantiation
            # during loading will not result in an import cycle.
            self.__class__._loaded = True
            self.__class__._dist_plugin_definitions = DistributionNameDict()
            self.read_entry_points()
            self.load()

    @property
    def distribution_plugin_definitions(self) -> Dict[str, DistributionPluginDefinition]:
        """Stores plugin definitions with distribution names as dict keys."""
        return self._dist_plugin_definitions.copy()

    def get_distribution_plugin_definition(
        self, dist_name: str = None
    ) -> DistributionPluginDefinition:
        """
        :param dist_name: needed if more than one distribution with FAST-OAD plugin is installed.
        :return: the DistributionPluginDefinition instance that matches `dist_name`, if any
        :raise FastNoDistPluginError: if no distribution with plugin is available.
        :raise FastSeveralDistPluginsError: if several distributions are available but `dist_name`
                                        has not been provided.
        :raise FastUnknownDistPluginError: if the specified distribution is not available.
        """

        if len(self._dist_plugin_definitions) == 0:
            raise FastNoDistPluginError()

        if dist_name is None:
            if len(self._dist_plugin_definitions) > 1:
                raise FastSeveralDistPluginsError()
            return next(iter(self._dist_plugin_definitions.values()))

        if dist_name not in self._dist_plugin_definitions:
            raise FastUnknownDistPluginError(dist_name)

        return self._dist_plugin_definitions[dist_name]

    def get_configuration_file_list(self, dist_name: str) -> List[ResourceInfo]:
        """
        :param dist_name: the distribution to inspect
        :return: list of configuration files available for named distribution,
                 or an empty list if the specified distribution is not available
        """
        return self._get_resource_list(
            DistributionPluginDefinition.get_configuration_file_list,
            dist_name,
        )

    def get_source_data_file_list(self, dist_name: str) -> List[ResourceInfo]:
        """
        :param dist_name: the distribution to inspect
        :return: list of source data files available for named distribution, or an empty list if the
                 specified distribution is not available
        """
        return self._get_resource_list(
            DistributionPluginDefinition.get_source_data_file_list,
            dist_name,
        )

    def get_notebook_folder_list(self, dist_name: str = None) -> List[ResourceInfo]:
        """
        Returns the list of notebook folders available for named distribution
        and optionally the named plugin of this distribution.

        :param dist_name: the distribution to inspect
        :return: list of notebook folders available for named distribution,
                 or an empty list if the specified distribution is not available
        """
        return self._get_resource_list(
            DistributionPluginDefinition.get_notebook_folder_list,
            dist_name,
        )

    def _get_resource_list(self, method: Callable, dist_name: str = None) -> List[ResourceInfo]:
        infos = []
        if dist_name:
            if dist_name not in self._dist_plugin_definitions:
                raise FastUnknownDistPluginError(dist_name)
            dist_names = [dist_name]
        else:
            if len(self._dist_plugin_definitions) == 0:
                raise FastNoDistPluginError()
            dist_names = self._dist_plugin_definitions.keys()

        for name in dist_names:
            dist_plugin_definitions = self._dist_plugin_definitions[name]
            infos += method(dist_plugin_definitions)

        return infos

    @classmethod
    def read_entry_points(cls):
        """
        Reads definitions of declared plugins.
        """
        # Dev note: in src/conftest.py, wrapt is used to monkey patch
        # importlib_metadata.entry_points when unit testing plugin-related feature.
        # This will not work if `from importlib_metadata import entry_points`
        # is done at beginning of the file, because then, we will use a reference
        # to original `entry_points`, before it is patched by conftest.py

        for group in [OLD_MODEL_PLUGIN_ID, MODEL_PLUGIN_ID]:
            for entry_point in importlib_metadata.entry_points(group=group):
                dist_name = entry_point.dist.name
                if dist_name not in cls._dist_plugin_definitions:
                    cls._dist_plugin_definitions[dist_name] = DistributionPluginDefinition()
                plugin_dist = cls._dist_plugin_definitions[dist_name]
                plugin_dist.dist_name = dist_name
                plugin_dist.read_entry_point(entry_point, group)

    @classmethod
    def load(cls):
        """
        Loads declared plugins.
        """
        for dist_plugin_definitions in cls._dist_plugin_definitions.values():
            for plugin_name, plugin_def in dist_plugin_definitions.items():
                _LOGGER.info("Loading FAST-OAD plugin %s", plugin_name)
                cls._load_models(plugin_def)

    @classmethod
    def _load_models(cls, plugin_definition: PluginDefinition):
        """Loads models from plugin."""
        if SubPackageNames.MODELS in plugin_definition.subpackages:
            _LOGGER.debug("   Loading models")
            BundleLoader().explore_folder(
                plugin_definition.subpackages[SubPackageNames.MODELS], is_package=True
            )
            Variable.read_variable_descriptions(
                plugin_definition.subpackages[SubPackageNames.MODELS]
            )
