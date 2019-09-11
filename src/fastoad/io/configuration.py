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
from typing import Union

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
            try:
                self._parse_problem_table(self, PROBLEM_TABLE_TAG, problem_definition)
            except BadOpenMDAOInstructionError as e:
                err = BadOpenMDAOInstructionError(e, PROBLEM_TABLE_TAG)
                _LOGGER.error(err)
                raise err

    def _parse_problem_table(self, component: Union[om.Problem, om.Group], identifier, table: dict):
        if not isinstance(table, dict):
            # TODO: raise correct exception
            raise Exception("incorrect problem definition")

        if identifier == PROBLEM_TABLE_TAG:
            group = component.model
        else:
            group = component

        if COMPONENT_ID_KEY in table:
            sub_component = OpenMDAOSystemFactory.get_system(table[COMPONENT_ID_KEY])
            group.add_subsystem(identifier, sub_component, promotes=['*'])
        else:
            for key, value in table.items():
                if isinstance(value, dict):
                    sub_component = group.add_subsystem(key, om.Group(), promotes=['*'])
                    try:
                        self._parse_problem_table(sub_component, key, value)
                    except BadOpenMDAOInstructionError as e:
                        raise BadOpenMDAOInstructionError(e, key)
                else:
                    try:
                        setattr(component, key, eval(value))
                    except Exception as e:
                        raise BadOpenMDAOInstructionError(e, key, value)

        return component


class BadOpenMDAOInstructionError(Exception):
    def __init__(self, original_exception: Exception, key, value=None):
        if hasattr(original_exception, 'key'):
            self.key = '%s.%s' % (key, original_exception.key)
        else:
            self.key = key
        if hasattr(original_exception, 'value'):
            self.value = '%s.%s' % (value, original_exception.value)
        else:
            self.value = value
        if hasattr(original_exception, 'original_exception'):
            self.original_exception = original_exception.original_exception
        else:
            self.original_exception = original_exception
        super().__init__(self, 'Attribute or value not recognized : %s = "%s"\nOriginal error: %s' %
                         (self.key, self.value, self.original_exception))
