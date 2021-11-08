"""
Plugin system for declaration of FAST-OAD models.
"""
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

import logging
from dataclasses import dataclass

from pkg_resources import iter_entry_points

from fastoad.openmdao.variables import Variable
from ._bundle_loader import BundleLoader

_LOGGER = logging.getLogger(__name__)  # Logger for this module

MODEL_PLUGIN_ID = "fastoad_model"


@dataclass
class PluginDefinition:
    """
    Simple structure for storing plugin data.
    """

    module_path: str = ""
    notebook_path: str = ""
    conf_file_path: str = ""


class PluginManager:
    """
    Plugin manager for FAST-OAD.
    """

    plugin_definitions = {}

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

            if len(plugin_identifier) == 1:
                cls.plugin_definitions[plugin_name].module_path = entry_point.module_name
            elif plugin_identifier[1] == "notebooks":
                cls.plugin_definitions[plugin_name].notebook_path = entry_point.module_name
            elif plugin_identifier[1] == "configurations":
                cls.plugin_definitions[plugin_name].conf_file_path = entry_point.module_name
            else:
                raise RuntimeWarning(f"{plugin_name} is not a valid plugin declaration.")

    @classmethod
    def load(cls):
        """
        Loads models from declared plugins.
        """
        for plugin_name, plugin_def in cls.plugin_definitions.items():
            _LOGGER.info("Loading FAST-OAD plugin %s", plugin_name)
            BundleLoader().explore_folder(plugin_def.module_path, is_package=True)
            Variable.read_variable_descriptions(plugin_def.module_path)
