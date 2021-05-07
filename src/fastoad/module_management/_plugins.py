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

from pkg_resources import iter_entry_points

from fastoad.openmdao.variables import Variable
from ._bundle_loader import BundleLoader

_LOGGER = logging.getLogger(__name__)  # Logger for this module

MODEL_PLUGIN_ID = "fastoad_model"


def load_plugins():
    """
    Loads declared plugins.
    """
    for entry_point in iter_entry_points(MODEL_PLUGIN_ID):
        plugin_name = entry_point.name
        module_name = entry_point.module_name
        _LOGGER.info("Loading FAST-OAD plugin %s", plugin_name)
        BundleLoader().explore_folder(module_name, is_package=True)
        Variable.read_variable_descriptions(module_name)
