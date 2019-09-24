"""
Module for management of options and factorizing their definition.
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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

from openmdao.core.group import Group

ENGINE_LOCATION_OPTION = 'engine_location'
TAIL_TYPE_OPTION = 'tail_type'
AIRCRAFT_TYPE_OPTION = 'ac_type'
AIRCRAFT_FAMILY_OPTION = 'ac_family'
CABIN_SIZING_OPTION = 'cabin_sizing'


class OpenMdaoOptionDispatcherGroup(Group):
    """ Helper class for transmitting option values to subsystems during self.configure() """

    def configure(self):
        """ Update options for all subsystems """
        for key in self.options:
            value = self.options[key]
            for subsystem in self.system_iter():
                if key in subsystem.options:
                    subsystem.options[key] = value
