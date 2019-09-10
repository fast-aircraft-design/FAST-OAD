"""
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

import logging
import os.path as pth

import openmdao.api as om
import toml

from fastoad.module_management.openmdao_system_factory import OpenMDAOSystemFactory

# Logger for this module
_LOGGER = logging.getLogger(__name__)

FOLDERS_KEY = 'module_folders'
PROBLEM_TABLE_TAG = 'problem'
COMPONENT_ID_KEY = 'id'


class ConfiguredProblem(om.Problem):

    def load(self, conf_filename):

        conf_dirname = pth.dirname(conf_filename)
        toml_dict = toml.load(conf_filename)
        module_folder_paths = toml_dict.get(FOLDERS_KEY, [])
        for folder_path in module_folder_paths:
            if pth.isabs(folder_path):
                OpenMDAOSystemFactory.explore_folder(folder_path)
            else:
                OpenMDAOSystemFactory.explore_folder(pth.join(conf_dirname, folder_path))

        problem_definition = toml_dict.get(PROBLEM_TABLE_TAG)
        if not problem_definition:
            # TODO: raise correct exception
            raise Exception("no problem defined")
        else:
            self.model = self._parse_problem_table(problem_definition)

    def _parse_problem_table(self, table):
        if not isinstance(table, dict):
            # TODO: raise correct exception
            raise Exception("incorrect problem definition")

        if COMPONENT_ID_KEY in table:
            component = OpenMDAOSystemFactory.get_system(table[COMPONENT_ID_KEY])
        else:
            component = om.Group()
            for key, value in table.items():
                if isinstance(value, dict):
                    sub_component = self._parse_problem_table(value)
                    component.add_subsystem(key, sub_component, promotes=['*'])
                else:
                    setattr(component, key, eval(value))

        return component
