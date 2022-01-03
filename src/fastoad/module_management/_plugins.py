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
from dataclasses import dataclass, field
from typing import Dict, List, Set

from pkg_resources import iter_entry_points

from fastoad.openmdao.variables import Variable
from ._bundle_loader import BundleLoader
from .._utils.resource_management.contents import PackageReader

_LOGGER = logging.getLogger(__name__)  # Logger for this module

OLD_MODEL_PLUGIN_ID = "fastoad_model"
MODEL_PLUGIN_ID = "fastoad"


@dataclass
class PluginDefinition:
    """
    Simple structure for storing plugin data.
    """

    package_name: str = ""
    subpackages: Dict = field(default_factory=dict)
    conf_files: Set = field(default_factory=set)
    dist_name: str = ""

    def detect_submodules(self):
        package = PackageReader(self.package_name)
        for subpackage_name in ["models", "notebooks", "configurations"]:
            if subpackage_name in package.contents:
                self.subpackages[subpackage_name] = ".".join([self.package_name, subpackage_name])


class FastoadLoader(BundleLoader):
    """
    Specialized :class:`BundleLoader` that will load plugins at first instantiation.

    This class should be instantiated whenever plugins need to be loaded, which
    also means whenever it is needed to know about registered models.
    """

    # This class attribute is private and is accessed through a property to ensure
    # that the class has been instantiated before the attribute is used.
    _plugin_definitions: Dict[str, PluginDefinition] = {}

    _loaded = False

    def __init__(self):
        super().__init__()
        if not self.__class__._loaded:
            # Setting cls.loaded to True already ensures that a second instantiation
            # during loading will not result in an import cycle.
            self.__class__._loaded = True
            self.read_entry_points()
            self.load()

    @property
    def plugin_definitions(self) -> Dict[str, PluginDefinition]:
        """
        Stores plugin definitions with plugin name as dict keys.
        """
        return self._plugin_definitions

    @classmethod
    def read_entry_points(cls):
        """
        Reads definitions of declared plugins.
        """
        for entry_point in iter_entry_points(OLD_MODEL_PLUGIN_ID):
            plugin_name = entry_point.name
            plugin_definition = PluginDefinition()
            plugin_definition.package_name = entry_point.module_name
            plugin_definition.subpackages["models"] = entry_point.module_name
            plugin_definition.dist_name = entry_point.dist.project_name
            cls._plugin_definitions[plugin_name] = plugin_definition

        for entry_point in iter_entry_points(MODEL_PLUGIN_ID):
            plugin_name = entry_point.name
            plugin_definition = PluginDefinition()
            plugin_definition.package_name = entry_point.module_name
            plugin_definition.detect_submodules()
            cls._plugin_definitions[plugin_name] = plugin_definition

    @classmethod
    def load(cls):
        """
        Loads declared plugins.
        """
        for plugin_name, plugin_def in cls._plugin_definitions.items():
            _LOGGER.info("Loading FAST-OAD plugin %s", plugin_name)
            cls._load_models(plugin_def)
            cls._load_configurations(plugin_def)

    @classmethod
    def get_configuration_file_list(cls, plugin_name=None) -> Dict[str, List[str]]:
        """
        Builds the list of sample configuration files provided with plugins.

        :param plugin_name: if provided, only files for this plugin will be returned
        :return: a dict with plugin name as keys, and list of files as values
        """
        file_lists = {}
        for name, plugin_definition in cls._plugin_definitions.items():
            if plugin_name is None or plugin_name == name:
                conf_files = [
                    file
                    for file in PackageReader(
                        plugin_definition.subpackages["configurations"]
                    ).contents
                    if pth.splitext(file)[1] in [".yml", ".yaml"]
                ]
                file_lists[name] = conf_files

        return file_lists

    @classmethod
    def _load_models(cls, plugin_definition: PluginDefinition):
        """Loads models from plugin."""
        if plugin_definition.subpackages["models"]:
            _LOGGER.debug("   Loading models")
            BundleLoader().explore_folder(plugin_definition.subpackages["models"], is_package=True)
            Variable.read_variable_descriptions(plugin_definition.subpackages["models"])

    @classmethod
    def _load_configurations(cls, plugin_definition: PluginDefinition):
        """Loads configurations from plugin."""
        package = PackageReader(plugin_definition.subpackages["configurations"])
        if package.is_package:
            _LOGGER.debug("   Loading configurations")
            for file_name in package.contents:
                file_ext = pth.splitext(file_name)[-1]
                if file_ext in [".yml", ".yaml"]:
                    plugin_definition.conf_files.add(file_name)
