"""
Exception for cmd package
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

from fastoad.exceptions import FastError


class FastFileExistsError(FastError):
    """Raised when asked for writing a file that already exists"""

    def __init__(self, *args):
        super().__init__(*args)
        self.file_path = args[1]


class FastUnknownPluginError(FastError):
    """Raised when a plugin name is not found."""

    def __init__(self, plugin_name):
        self.plugin_name = plugin_name
        super().__init__(f'No plugin found with name "{plugin_name}"')


class FastUnknownConfigurationFileError(FastError):
    """Raised when a configuration file is not found for named plugin."""

    def __init__(self, configuration_file, plugin_name):
        self.configuration_file = configuration_file
        self.plugin_name = plugin_name
        super().__init__(
            f'Configuration file "{configuration_file}" not provided with plugin "{plugin_name}"'
        )


class FastSeveralConfigurationFilesError(FastError):
    """
    Raised when no configuration file has been specified but several configuration files are
    provided with the plugin."""

    def __init__(self, plugin_name):
        self.plugin_name = plugin_name
        super().__init__(
            f'Plugin "{plugin_name}" provides several configuration files. One must be specified."'
        )
