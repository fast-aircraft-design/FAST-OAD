"""
Plugin system for module declaration.
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
from importlib.resources import open_text, contents
from types import ModuleType
from typing import Dict

from pkg_resources import iter_entry_points

from fastoad.openmdao.variables import DESCRIPTION_FILENAME, Variable
from .bundle_loader import BundleLoader

_LOGGER = logging.getLogger(__name__)  # Logger for this module

MODEL_PLUGIN_ID = "fastoad_model"


def load_plugins() -> Dict[str, ModuleType]:
    """
    Loads declared plugins.

    :return: dictionary (plugin name, module)
    """
    # Loading plugins
    discovered_plugins = {
        entry_point.name: entry_point.load() for entry_point in iter_entry_points(MODEL_PLUGIN_ID)
    }
    for plugin_name, package in discovered_plugins.items():
        _recursive_load(package.__name__)
        _LOGGER.info("Loaded FAST-OAD plugin %s", plugin_name)
        if DESCRIPTION_FILENAME in contents(package):
            try:
                with open_text(package, DESCRIPTION_FILENAME) as desc_io:
                    Variable.read_variable_descriptions(desc_io)
                _LOGGER.info("Loaded variable descriptions from plugin %s", plugin_name)
            except Exception as exc:
                _LOGGER.error(
                    "Could not read variable description for plugin %s. Error log is:\n%s",
                    plugin_name,
                    exc,
                )
        else:
            _LOGGER.info("No variable description in plugin %s", plugin_name)

    return discovered_plugins


def _recursive_load(package_name: str):
    """
    Recursively loads indicated package, which will register all classes that are decorated
    with an iPOPO decorator or a RegisterSystem.

    :param package_name:
    """
    try:
        package_contents = contents(package_name)
    except (TypeError, ModuleNotFoundError):
        if package_name.endswith(".py"):
            try:
                bundle = BundleLoader().context.install_bundle(package_name[:-3])
                bundle.stop()
                bundle.start()
                _LOGGER.info("Loaded %s" % package_name)
            except:  # There can be plenty of good reasons to fail, so we just log it.
                _LOGGER.info("Ignored %s" % package_name)

        return

    for item in package_contents:
        _recursive_load(".".join([package_name, item]))
