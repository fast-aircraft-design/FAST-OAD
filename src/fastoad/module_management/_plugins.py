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
import warnings
from dataclasses import dataclass, field
from typing import Dict, Set

from pkg_resources import iter_entry_points

from fastoad.openmdao.variables import Variable
from ._bundle_loader import BundleLoader
from .._utils.resource_management.contents import PackageReader

_LOGGER = logging.getLogger(__name__)  # Logger for this module

MODEL_PLUGIN_ID = "fastoad_model"


@dataclass
class PluginDefinition:
    """
    Simple structure for storing plugin data.
    """

    module_package_name: str = ""
    notebook_package_name: str = ""
    conf_file_package_name: str = ""
    conf_files: Set = field(default_factory=set)
    dist_name: str = ""


class FastoadLoader(BundleLoader):
    """
    Specialized :class:`BundleLoader` that will load plugins at first instantiation.

    This class should be instantiated whenever plugins need to be loaded, which
    also means whenever registered models need to be known.
    """

    #: Stores plugin definitions with plugin name as dict key.
    plugin_definitions: Dict[str, PluginDefinition] = {}

    _loaded = False

    def __init__(self):
        super().__init__()
        if not self.__class__._loaded:
            # Setting cls.loaded to True already ensures that a second instantiation
            # during loading will not result in an import cycle.
            self.__class__._loaded = True
            self.read_entry_points()
            self.load()

    @classmethod
    def read_entry_points(cls):
        """
        Reads definitions of declared plugins.
        """
        for entry_point in iter_entry_points(MODEL_PLUGIN_ID):
            plugin_identifier = entry_point.name.split(".")

            plugin_name = plugin_identifier[0]
            if plugin_name not in cls.plugin_definitions:
                cls.plugin_definitions[plugin_name] = PluginDefinition()
                cls.plugin_definitions[plugin_name].dist_name = entry_point.dist.project_name

            if len(plugin_identifier) == 1:
                # Location of models.
                # The existence is checked later and more in details.
                cls.plugin_definitions[plugin_name].module_package_name = entry_point.module_name
            elif not PackageReader(entry_point.module_name).is_package:
                # For other parts of the plugin, we check already the existence.
                warnings.warn(
                    f"{entry_point.module_name} (defined by library "
                    f"{entry_point.dist.project_name}) is not a valid package name.",
                    RuntimeWarning,
                )
                continue
            elif plugin_identifier[1] == "notebooks":
                cls.plugin_definitions[plugin_name].notebook_package_name = entry_point.module_name
            elif plugin_identifier[1] == "configurations":
                cls.plugin_definitions[plugin_name].conf_file_package_name = entry_point.module_name
            else:
                warnings.warn(f"{plugin_name} is not a valid plugin declaration.", RuntimeWarning)

    @classmethod
    def load(cls):
        """
        Loads declared plugins.
        """
        for plugin_name, plugin_def in cls.plugin_definitions.items():
            _LOGGER.info("Loading FAST-OAD plugin %s", plugin_name)
            cls._load_models(plugin_def)
            cls._load_configurations(plugin_def)

    @classmethod
    def _load_models(cls, plugin_definition: PluginDefinition):
        """Loads models from plugin."""
        if plugin_definition.module_package_name:
            _LOGGER.debug("   Loading models")
            BundleLoader().explore_folder(plugin_definition.module_package_name, is_package=True)
            Variable.read_variable_descriptions(plugin_definition.module_package_name)

    @classmethod
    def _load_configurations(cls, plugin_definition: PluginDefinition):
        """Loads configurations from plugin."""
        package = PackageReader(plugin_definition.conf_file_package_name)
        if package.is_package:  # Checking it is not None
            _LOGGER.debug("   Loading configurations")
            for file_name in package.contents:
                file_ext = pth.splitext(file_name)[-1]
                if file_ext in [".yml", ".yaml"]:
                    plugin_definition.conf_files.add(file_name)
