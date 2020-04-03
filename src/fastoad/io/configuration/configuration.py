"""
Module for building OpenMDAO problem from configuration file
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

import logging
import os.path as pth
from copy import deepcopy

import openmdao.api as om
import toml
from fastoad.io.configuration.exceptions import (
    FASTConfigurationBaseKeyBuildingError,
    FASTConfigurationBadOpenMDAOInstructionError,
    FASTConfigurationNoProblemDefined,
)
from fastoad.io.serialize import OMFileIOSubclass
from fastoad.io.xml import OMXmlIO
from fastoad.module_management import OpenMDAOSystemRegistry
from fastoad.openmdao.utils import (
    get_unconnected_input_variables,
    get_variables_from_ivc,
    get_ivc_from_variables,
    get_variables_from_problem,
)

# Logger for this module
INPUT_SYSTEM_NAME = "inputs"
_LOGGER = logging.getLogger(__name__)

KEY_FOLDERS = "module_folders"
KEY_INPUT_FILE = "input_file"
KEY_OUTPUT_FILE = "output_file"
KEY_COMPONENT_ID = "id"
TABLE_MODEL = "model"
KEY_DRIVER = "driver"
TABLES_DESIGN_VAR = "design_var"
TABLES_OBJECTIVE = "objective"
TABLES_CONSTRAINT = "constraint"


class FASTOADProblem(om.Problem):
    """
    Vanilla OpenMDAO Problem except that its definition can be loaded from
    a TOML file.

    A classical usage of this class will be::

        problem = FASTOADProblem()  # instantiation
        problem.configure('my_problem.toml')  # reads problem definition
        problem.write_needed_inputs()  # writes the input file (defined in problem definition) with
                                       # needed variables so user can fill it with proper values
        # or
        problem.write_needed_inputs('previous.xml')  # writes the input file with needed variables
                                                     # and values taken from provided file when
                                                     # available
        problem.read_inputs()    # reads the input file
        problem.run_driver()     # runs the OpenMDAO problem
        problem.write_outputs()  # writes the output file (defined in problem definition)

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.optim_failed = False
        """ Tells if last optimization (run_driver) failed """

        self._conf_dict = {}
        self.input_file_path = None
        self.output_file_path = None
        self._model_definition = None

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
        #        producing errors if missing definition of data I/O files

        # I/O files
        input_file = self._conf_dict.get(KEY_INPUT_FILE)
        if input_file:
            self.input_file_path = pth.join(conf_dirname, input_file)

        output_file = self._conf_dict.get(KEY_OUTPUT_FILE)
        if output_file:
            self.output_file_path = pth.join(conf_dirname, output_file)

        # Looking for modules to register
        module_folder_paths = self._conf_dict.get(KEY_FOLDERS, [])
        for folder_path in module_folder_paths:
            folder_path = pth.join(conf_dirname, folder_path)
            if not pth.exists(folder_path):
                _LOGGER.warning("SKIPPED %s: it does not exist.")
            else:
                OpenMDAOSystemRegistry.explore_folder(folder_path)

        # Read problem definition
        self._model_definition = self._conf_dict.get(TABLE_MODEL)
        if not self._model_definition:
            raise FASTConfigurationNoProblemDefined("Section [%s] is missing" % TABLE_MODEL)

        # Define driver
        driver = self._conf_dict.get(KEY_DRIVER, "")
        if driver:
            self.driver = _om_eval(driver)

        self.build_model()

    def write_needed_inputs(self, input_data: OMFileIOSubclass = None):
        """
        Writes the input file of the problem with unconnected inputs of the configured problem.

        Written value of each variable will be taken:
        1. from input_data if it contains the variable
        2. from defined default values in component definitions

        WARNING: if inputs have already been read, they won't be needed any more and won't be
        in written file. To clear read data, use first :meth:`build_problem`.

        :param input_data: if provided, variable values will be read from it, if available.
        """
        if self.input_file_path:
            variables = get_unconnected_input_variables(self, with_optional_inputs=True)
            if input_data:
                ref_ivc = input_data.read()
                ref_vars = get_variables_from_ivc(ref_ivc)
                variables.update(ref_vars)
            writer = OMXmlIO(self.input_file_path)
            writer.write(get_ivc_from_variables(variables))

    def read_inputs(self):
        """
        Reads inputs from the configured input file.

        Must be done once problem is configured, before self.setup() is called.
        """
        if self.input_file_path:
            # Reads input file
            reader = OMXmlIO(self.input_file_path)
            ivc = reader.read()

            # ivc will be added through add_subsystem, but we must use set_order() to
            # put it first.
            # So we need order of existing subsystem to provide the full order list to set_order()
            # To get order of systems, we use system_iter() that can be used only after setup().
            # But we will not be allowed to use add_subsystem() after setup().
            # So we use setup() on a copy of current instance, and get order from this copy
            tmp_prob = deepcopy(self)
            tmp_prob.setup()
            previous_order = [system.name for system in tmp_prob.model.system_iter(recurse=False)]

            self.model.add_subsystem(INPUT_SYSTEM_NAME, ivc, promotes=["*"])
            self.model.set_order([INPUT_SYSTEM_NAME] + previous_order)

            # Inputs are loaded, so we can add design variables
            self._add_design_vars()

    def write_outputs(self):
        """
        Once problem is run, writes all outputs in the configured output file.
        """
        if self.output_file_path:
            writer = OMXmlIO(self.output_file_path)
            variables = get_variables_from_problem(self)
            writer.write(get_ivc_from_variables(variables))

    def build_model(self):
        """
        Builds (or rebuilds) the problem as defined in the configuration file.

        self.model is initialized as a new group and populated subsystems indicated in
        configuration file.
        """

        self.model = om.Group()

        try:
            if KEY_COMPONENT_ID in self._model_definition:
                # The defined model is only one system
                system_id = self._model_definition[KEY_COMPONENT_ID]
                sub_component = OpenMDAOSystemRegistry.get_system(system_id)
                self.model.add_subsystem("system", sub_component, promotes=["*"])
            else:
                # The defined model is a group
                self._parse_problem_table(self.model, self._model_definition)

        except FASTConfigurationBaseKeyBuildingError as err:
            log_err = err.__class__(err, TABLE_MODEL)
            _LOGGER.error(log_err)
            raise log_err

        self._add_objectives()
        self._add_constraints()

    def _parse_problem_table(self, group: om.Group, table: dict):
        """
        Feeds provided *group*, using definition in provided TOML *table*.

        :param group:
        :param table:
        """
        assert isinstance(table, dict), "table should be a dictionary"

        for key, value in table.items():
            if isinstance(value, dict):  # value defines a sub-component
                if KEY_COMPONENT_ID in value:
                    # It is a non-group component, that should be registered with its ID
                    options = value.copy()
                    identifier = options.pop(KEY_COMPONENT_ID)
                    sub_component = OpenMDAOSystemRegistry.get_system(identifier, options=options)
                    group.add_subsystem(key, sub_component, promotes=["*"])
                else:
                    # It is a Group
                    sub_component = group.add_subsystem(key, om.Group(), promotes=["*"])
                    try:
                        self._parse_problem_table(sub_component, value)
                    except FASTConfigurationBadOpenMDAOInstructionError as err:
                        # There has been an error while parsing an attribute.
                        # Error is relayed with key added for context
                        raise FASTConfigurationBadOpenMDAOInstructionError(err, key)
            else:
                # value is an attribute of current component and will be literally interpreted
                try:
                    setattr(group, key, _om_eval(value))  # pylint:disable=eval-used
                except Exception as err:
                    raise FASTConfigurationBadOpenMDAOInstructionError(err, key, value)

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
        """ Adds design variables as instructed in configuration file """
        design_var_tables = self._conf_dict.get(TABLES_DESIGN_VAR, [])
        for design_var_table in design_var_tables:
            self.model.add_design_var(**design_var_table)


def _om_eval(string_to_eval: str):
    """
    Evaluates strings that assume `import openmdao.api as om` is done.

    eval() is used for that, as safely as possible.

    :param string_to_eval:
    :return: result of eval()
    """
    if "__" in string_to_eval:
        raise ValueError("No double underscore allowed in evaluated string for security reasons")
    return eval(string_to_eval, {"__builtins__": {}}, {"om": om})
