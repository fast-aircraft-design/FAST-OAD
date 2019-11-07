"""
Module for building OpenMDAO problem from configuration file
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

from fastoad.io.configuration.exceptions import FASTConfigurationBaseKeyBuildingError, \
    FASTConfigurationBadOpenMDAOInstructionError, FASTConfigurationNoProblemDefined
from fastoad.io.serialize import OMFileIOSubclass
from fastoad.io.xml import OMXmlIO
from fastoad.module_management.openmdao_system_factory import OpenMDAOSystemFactory
# Logger for this module
from fastoad.openmdao.connections_utils import build_ivc_of_variables, \
    build_ivc_of_unconnected_inputs, update_ivc

_LOGGER = logging.getLogger(__name__)

KEY_FOLDERS = 'module_folders'
KEY_INPUT_FILE = 'input_file'
KEY_OUTPUT_FILE = 'output_file'
KEY_COMPONENT_ID = 'id'
TABLE_PROBLEM = 'problem'
TABLES_DESIGN_VAR = 'design_var'
TABLES_OBJECTIVE = 'objective'
TABLES_CONSTRAINT = 'constraint'


class ConfiguredProblem(om.Problem):
    """
    Vanilla OpenMDAO Problem except that its definition can be loaded from
    a TOML file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._conf_dict = {}
        self._input_file = None
        self._output_file = None

    def configure(self, conf_file):
        """
        Reads definition of the current problem in given file.

        :param conf_file: Path to the file to open or a file descriptor
        """
        # Dev note: toml.load would also accept an array of files as input, but
        # it does not look useful for us, so it is not mentioned in docstring.

        conf_dirname = pth.dirname(pth.abspath(conf_file))  # for resolving relative paths
        self._conf_dict = toml.load(conf_file)

        # FIXME: Structure of configuration file will have to be checked more thoroughly, like
        #        producing errors if missing data I/O files

        # I/O files
        input_file = self._conf_dict.get(KEY_INPUT_FILE)
        if input_file:
            self._input_file = pth.join(conf_dirname, input_file)

        output_file = self._conf_dict.get(KEY_OUTPUT_FILE)
        if output_file:
            self._output_file = pth.join(conf_dirname, output_file)

        # Looking for modules to register
        module_folder_paths = self._conf_dict.get(KEY_FOLDERS, [])
        for folder_path in module_folder_paths:
            folder_path = pth.join(conf_dirname, folder_path)
            if not pth.exists(folder_path):
                _LOGGER.warning('SKIPPED %s: it does not exist.')
            else:
                OpenMDAOSystemFactory.explore_folder(folder_path)

        # Read problem definition
        problem_definition = self._conf_dict.get(TABLE_PROBLEM)
        if not problem_definition:
            raise FASTConfigurationNoProblemDefined("Section [%s] is missing" % TABLE_PROBLEM)

        try:
            self._parse_problem_table(self, TABLE_PROBLEM, problem_definition)
        except FASTConfigurationBaseKeyBuildingError as err:
            log_err = err.__class__(err, TABLE_PROBLEM)
            _LOGGER.error(log_err)
            raise log_err

        # Objectives and constraints are based on problem outputs, so concerned variables
        # are expected to be defined by now (unlike design variables that will be
        # defined after reading inputs)
        self._add_objectives()
        self._add_constraints()

        self.setup()

    def write_needed_inputs(self, input_data: OMFileIOSubclass = None):
        """
        Once problem is configured, creates the configured input file with all
        needed inputs of the problem, with default values taken from component
        definitions.
        """
        if self._input_file:
            ivc = build_ivc_of_unconnected_inputs(self)
            if input_data:
                ref_ivc = input_data.read()
                ivc = update_ivc(ivc, ref_ivc)
            writer = OMXmlIO(self._input_file)
            writer.write(ivc)

    def read_inputs(self):
        """
        Once problem is configured, reads inputs from the configured input file.
        """
        if self._input_file:
            reader = OMXmlIO(self._input_file)
            self.model.add_subsystem('inputs', reader.read(), promotes=['*'])

            # Now all variables should be available, design vars can be defined.
            self._add_design_vars()

            self.setup()

    def write_outputs(self):
        """
        Once problem is run, writes all outputs in the configured output file.
        """
        if self._output_file:
            writer = OMXmlIO(self._output_file)
            ivc = build_ivc_of_variables(self.model)
            writer.write(ivc)

    def _parse_problem_table(self, component: Union[om.Problem, om.Group], identifier, table: dict):
        """
        Feeds provided *component*, associated to provided *identifier*, using definition
        in provided TOML *table*.

        :param component:
        :param identifier:
        :param table:
        """
        assert isinstance(table, dict), "table should be a dictionary"

        if identifier == TABLE_PROBLEM:  # component is a Problem
            group = component.model
        else:  # component is a Group
            assert isinstance(component, om.Group)
            group = component

        # Assessing sub-components
        if KEY_COMPONENT_ID in table:  # table defines a non-Group component
            sub_component = OpenMDAOSystemFactory.get_system(table[KEY_COMPONENT_ID])
            group.add_subsystem(identifier, sub_component, promotes=['*'])
        else:
            for key, value in table.items():
                if isinstance(value, dict):  # value defines a sub-component
                    sub_component = group.add_subsystem(key, om.Group(), promotes=['*'])
                    try:
                        self._parse_problem_table(sub_component, key, value)
                    except FASTConfigurationBadOpenMDAOInstructionError as err:
                        # There has been an error while parsing an attribute.
                        # Error is relayed with key added for context
                        raise FASTConfigurationBadOpenMDAOInstructionError(err, key)
                else:
                    # value is an attribute of current component and will be literally interpreted
                    try:
                        # FIXME: remove this eval()
                        setattr(component, key, eval(value))  # pylint:disable=eval-used
                    except Exception as err:
                        raise FASTConfigurationBadOpenMDAOInstructionError(err, key, value)

        return component

    def _add_constraints(self):
        """  Adds constraints as instructed in configuration file """
        # Constraints
        constraint_tables = self._conf_dict.get(TABLES_CONSTRAINT, [])
        for constraint_table in constraint_tables:
            self.model.add_constraint(**constraint_table)

    def _add_objectives(self):
        """  Adds objectives as instructed in configuration file """
        objective_tables = self._conf_dict.get(TABLES_OBJECTIVE, [])
        for objective_table in objective_tables:
            self.model.add_objective(**objective_table)

    def _add_design_vars(self):
        """  Adds design variables as instructed in configuration file """
        design_var_tables = self._conf_dict.get(TABLES_DESIGN_VAR, [])
        for design_var_table in design_var_tables:
            self.model.add_design_var(**design_var_table)
