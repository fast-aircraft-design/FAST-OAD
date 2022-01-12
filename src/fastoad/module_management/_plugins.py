"""
Plugin system for declaration of FAST-OAD models.
"""
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

import logging
import os.path as pth
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Union

from fastoad.openmdao.variables import Variable
from ._bundle_loader import BundleLoader
from .._utils.resource_management.contents import PackageReader

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points, EntryPoint
else:
    from importlib.metadata import entry_points, EntryPoint

_LOGGER = logging.getLogger(__name__)  # Logger for this module

OLD_MODEL_PLUGIN_ID = "fastoad_model"
MODEL_PLUGIN_ID = "fastoad.plugins"


@dataclass
class PluginDefinition:
    """
    Stores and provides FAST-OAD plugin data.
    """

    dist_name: str
    plugin_name: str
    package_name: str = ""
    subpackages: Dict = field(default_factory=dict)
    conf_files: Set = field(default_factory=set)

    def detect_subfolders(self):
        """
        Scans plugin folders and populates :attr:`subpackages`.
        """
        package = PackageReader(self.package_name)
        for subpackage_name in ["models", "notebooks", "configurations"]:
            if subpackage_name in package.contents:
                self.subpackages[subpackage_name] = ".".join([self.package_name, subpackage_name])

    def get_configuration_file_list(self) -> List[str]:
        """
        :return: List of configuration file names that are provided by the plugin.
        """
        if "configurations" in self.subpackages:
            return [
                file
                for file in PackageReader(self.subpackages["configurations"]).contents
                if pth.splitext(file)[1] in [".yml", ".yaml"]
            ]

        return []


@dataclass()
class DistributionPluginDefinition(dict):
    """
    Stores and provides data for FAST-OAD plugins provided by a Python distribution.
    """

    dist_name: str = None

    def read_entry_point(self, entry_point: EntryPoint, group: str):
        """
        Adds plugin definition from provided entry point to

        Does nothing if entry_point.dist.project_name is not equal to :attr:`dist_name`

        :param entry_point:
        :param group:
        """
        if self.dist_name != entry_point.dist.name:
            return

        plugin_definition = PluginDefinition(
            dist_name=self.dist_name,
            plugin_name=entry_point.name,
        )
        plugin_definition.package_name = entry_point.module
        self[entry_point.name] = plugin_definition

        if group == OLD_MODEL_PLUGIN_ID:
            self[entry_point.name].subpackages["models"] = entry_point.module

        if group == MODEL_PLUGIN_ID:
            self[entry_point.name].detect_subfolders()

    def get_configuration_file_list(self, plugin_name=None):
        """
        :param plugin_name: If provided, only file names provided by the plugin in
                            the distribution will be returned, or an empty list if
                            the plugin is not in the distribution.
        :return:  List of configuration file names that are provided by the distribution.
        """
        file_list = []
        if plugin_name:
            if plugin_name in self:
                file_list = self[plugin_name].get_configuration_file_list()
        else:
            for plugin in self.values():
                file_list += plugin.get_configuration_file_list()

        return file_list


class FastoadLoader(BundleLoader):
    """
    Specialized :class:`BundleLoader` that will load plugins at first instantiation.

    This class should be instantiated whenever plugins need to be loaded, which
    also means whenever it is needed to know about registered models.
    """

    # This class attribute is private and is accessed through a property to ensure
    # that the class has been instantiated before the attribute is used.
    _plugin_definitions: Dict[str, DistributionPluginDefinition]

    _loaded = False

    def __init__(self):
        super().__init__()
        if not self.__class__._loaded:
            # Setting cls.loaded to True already ensures that a second instantiation
            # during loading will not result in an import cycle.
            self.__class__._loaded = True
            self.__class__._plugin_definitions = defaultdict(DistributionPluginDefinition)
            self.read_entry_points()
            self.load()

    @property
    def plugin_definitions(self) -> Dict[str, Dict[str, PluginDefinition]]:
        """
        Stores plugin definitions with plugin name as dict keys.
        """
        return self._plugin_definitions

    @classmethod
    def read_entry_points(cls):
        """
        Reads definitions of declared plugins.
        """
        for group in [OLD_MODEL_PLUGIN_ID, MODEL_PLUGIN_ID]:
            for entry_point in entry_points(group=group):
                plugin_dist = cls._plugin_definitions[entry_point.dist.name]
                plugin_dist.dist_name = entry_point.dist.name
                plugin_dist.read_entry_point(entry_point, group)

    @classmethod
    def load(cls):
        """
        Loads declared plugins.
        """
        for plugin_dist, dist_plugin_definitions in cls._plugin_definitions.items():
            for plugin_name, plugin_def in dist_plugin_definitions.items():
                _LOGGER.info("Loading FAST-OAD plugin %s", plugin_name)
                cls._load_models(plugin_def)
                cls._load_configurations(plugin_def)

    @classmethod
    def get_configuration_file_list(
        cls, plugin_distribution: str, plugin_name: str = None, with_plugin_name: bool = True
    ) -> List[Union[str, Tuple[str, str]]]:
        """
        Returns the list of configuration files available for named distribution (the
        Python library) and optionally the named plugin of this distribution.

        :param plugin_distribution: the Python library to inspect
        :param plugin_name: if provided, only the files for the defined plugin will be returned
        :param with_plugin_name: if True, the returned list will be tuples (configuration file,
                                 plugin name). If False, only configuration file names will be
                                 returned
        :return: list of configuration files provided by specified plugin,
                 or an empty list if the specified plugin is not available
        """
        dist_plugin_definitions = cls._plugin_definitions[plugin_distribution]
        if plugin_name:
            plugin_names = [plugin_name]
        else:
            plugin_names = dist_plugin_definitions.keys()

        file_lists = {
            plugin_name: dist_plugin_definitions.get_configuration_file_list(plugin_name)
            for plugin_name in plugin_names
        }

        file_list = []
        for plugin_name, files in file_lists.items():
            if with_plugin_name:
                file_list += [(file_name, plugin_name) for file_name in files]
            else:
                file_list += files

        return file_list

    @classmethod
    def _load_models(cls, plugin_definition: PluginDefinition):
        """Loads models from plugin."""
        if "models" in plugin_definition.subpackages:
            _LOGGER.debug("   Loading models")
            BundleLoader().explore_folder(plugin_definition.subpackages["models"], is_package=True)
            Variable.read_variable_descriptions(plugin_definition.subpackages["models"])

    @classmethod
    def _load_configurations(cls, plugin_definition: PluginDefinition):
        """Loads configurations from plugin."""
        if "configurations" in plugin_definition.subpackages:
            _LOGGER.debug("   Loading configurations")
            package = PackageReader(plugin_definition.subpackages["configurations"])
            for file_name in package.contents:
                file_ext = pth.splitext(file_name)[-1]
                if file_ext in [".yml", ".yaml"]:
                    plugin_definition.conf_files.add(file_name)
