"""
Module for management of options and factorizing their definition.
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

import openmdao.api as om

CABIN_SIZING_OPTION = "cabin_sizing"
PAYLOAD_FROM_NPAX = "payload_from_npax"


class OpenMdaoOptionDispatcherGroup(om.Group):
    """
    Helper class for transmitting option values to subsystems during self.configure()

    Just create a group by inheriting of this class instead of om.Group. Any option that is
    defined in the group will be transmitted to its immediate subsystems (no recursive
    behaviour), if they have the same option.
    """

    def configure(self):
        """ Update options for all subsystems """
        for key in self.options:
            value = self.options[key]
            for subsystem in self.system_iter(recurse=False):
                if key in subsystem.options:
                    subsystem.options[key] = value
