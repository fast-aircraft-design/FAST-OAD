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

from pkg_resources import iter_entry_points

_LOGGER = logging.getLogger(__name__)  # Logger for this module


def load_plugins():
    """
    Loads declared plugins.
    """
    # Loading plugins
    discovered_plugins = {
        entry_point.name: entry_point.load() for entry_point in iter_entry_points("fastoad.models")
    }
    for plugin_name in discovered_plugins:
        _LOGGER.info("Loaded FAST-OAD plugin %s", plugin_name)
