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
from typing import Dict

import openmdao.api as om
import tomlkit

from fastoad.io import IVariableIOFormatter
from fastoad.models.defaults import set_all_input_defaults
from fastoad.module_management import OpenMDAOSystemRegistry
from fastoad.openmdao.problem import FASTOADProblem
from fastoad.utils.files import make_parent_dir
from .exceptions import (
    FASTConfigurationBaseKeyBuildingError,
    FASTConfigurationBadOpenMDAOInstructionError,
    FASTConfigurationError,
)

_LOGGER = logging.getLogger(__name__)  # Logger for this module

KEY_FOLDERS = "module_folders"
KEY_INPUT_FILE = "input_file"
KEY_OUTPUT_FILE = "output_file"
KEY_COMPONENT_ID = "id"
TABLE_MODEL = "model"
KEY_DRIVER = "driver"
TABLE_OPTIMIZATION = "optimization"
TABLES_DESIGN_VAR = "design_var"
TABLES_CONSTRAINT = "constraint"
TABLES_OBJECTIVE = "objective"


class FASTOADProblemConfigurator:
    """
    class for configuring an OpenMDAO problem from a configuration file

    See :ref:`description of configuration file <configuration-file>`.

    :param conf_file_path: if provided, configuration will be read directly from it
    """

    def __init__(self, conf_file_path=None):
        self._conf_file = None
        self._conf_dict = {}

        if conf_file_path:
            self.load(conf_file_path)

    @property
    def input_file_path(self):
        """path of file with input variables of the problem"""
        path = self._conf_dict[KEY_INPUT_FILE]
        if not pth.isabs(path):
            path = pth.normpath(pth.join(pth.dirname(self._conf_file), path))
        return path

    @input_file_path.setter
    def input_file_path(self, file_path: str):
        self._conf_dict[KEY_INPUT_FILE] = file_path

    @property
    def output_file_path(self):
        """path of file where output variables will be written"""
        path = self._conf_dict[KEY_OUTPUT_FILE]
        if not pth.isabs(path):
            path = pth.normpath(pth.join(pth.dirname(self._conf_file), path))
        return path

    @output_file_path.setter
    def output_file_path(self, file_path: str):
        self._conf_dict[KEY_OUTPUT_FILE] = file_path

    def get_problem(self, read_inputs: bool = False, auto_scaling: bool = False) -> FASTOADProblem:
        """
        Builds the OpenMDAO problem from current configuration.

        :param read_inputs: if True, the created problem will already be fed
                            with variables from the input file
        :param auto_scaling: if True, automatic scaling is performed for design
                             variables and constraints
        :return: the problem instance
        """
        if not self._conf_dict:
            raise RuntimeError("read configuration file first")

        problem = FASTOADProblem(self._build_model())

        problem.input_file_path = self.input_file_path
        problem.output_file_path = self.output_file_path

        driver = self._conf_dict.get(KEY_DRIVER, "")
        if driver:
            problem.driver = _om_eval(driver)

        if self.get_optimization_definition():
            self._add_constraints(problem.model, auto_scaling)
            self._add_objectives(problem.model)

        if read_inputs:
            problem.read_inputs()
            self._add_design_vars(problem.model, auto_scaling)

        return problem

    def load(self, conf_file):
        """
        Reads the problem definition

        :param conf_file: Path to the file to open or a file descriptor
        """

        self._conf_file = pth.abspath(conf_file)

        conf_dirname = pth.dirname(pth.abspath(conf_file))  # for resolving relative paths
        with open(conf_file, "r") as file:
            d = file.read()
            self._conf_dict = tomlkit.loads(d)

        # FIXME: Could structure of configuration file be checked more thoroughly ?
        for key in [KEY_INPUT_FILE, KEY_OUTPUT_FILE]:
            if key not in self._conf_dict:
                raise FASTConfigurationError(missing_key=key)

        if not isinstance(self._conf_dict.get(TABLE_MODEL), dict):
            raise FASTConfigurationError(missing_section=TABLE_MODEL)

        # Looking for modules to register
        module_folder_paths = self._conf_dict.get(KEY_FOLDERS, [])
        for folder_path in module_folder_paths:
            folder_path = pth.join(conf_dirname, folder_path)
            if not pth.exists(folder_path):
                _LOGGER.warning("SKIPPED %s: it does not exist.")
            else:
                OpenMDAOSystemRegistry.explore_folder(folder_path)

    def save(self, filename: str = None):
        """
        Saves the current configuration
        If no filename is provided, the initially read file is used.

        :param filename: file where to save configuration
        """
        if not filename:
            filename = self._conf_file

        make_parent_dir(filename)
        with open(filename, "w") as file:
            d = tomlkit.dumps(self._conf_dict)
            file.write(d)

    def write_needed_inputs(
        self, source_file_path: str = None, source_formatter: IVariableIOFormatter = None,
    ):
        """
        Writes the input file of the problem with unconnected inputs of the
        configured problem.

        Written value of each variable will be taken:

            1. from input_data if it contains the variable
            2. from defined default values in component definitions

        :param source_file_path: if provided, variable values will be read from it
        :param source_formatter: the class that defines format of input file. if
                                 not provided, expected format will be the default one.
        """
        problem = self.get_problem(read_inputs=False)
        problem.write_needed_inputs(source_file_path, source_formatter)

    def get_optimization_definition(self) -> Dict:
        """
        Returns information related to the optimization problem:
            - Design Variables
            - Constraints
            - Objectives

        :return: dict containing optimization settings for current problem
        """

        optimization_definition = {}
        conf_dict = self._conf_dict.get(TABLE_OPTIMIZATION)
        if conf_dict:
            for sec, elements in conf_dict.items():
                optimization_definition[sec] = {elem["name"]: elem for elem in elements}
        return optimization_definition

    def set_optimization_definition(self, optimization_definition: Dict):
        """
        Updates configuration with the list of design variables, constraints, objectives
        contained in the optimization_definition dictionary.

        Keys of the dictionary are: "design_var", "constraint", "objective".

        Configuration file will not be modified until :meth:`write` is used.

        :param optimization_definition: dict containing the optimization problem definition
        """
        subpart = {}
        for key, value in optimization_definition.items():
            subpart[key] = [value for _, value in optimization_definition[key].items()]
        subpart = {"optimization": subpart}
        self._conf_dict.update(subpart)

    def _build_model(self) -> om.Group:
        """
        Builds the model as defined in the configuration file.

        The model is initialized as a new group and populated with subsystems
        indicated in configuration file.

        :return: the built model
        """

        model = om.Group()
        model_definition = self._conf_dict.get(TABLE_MODEL)

        try:
            if KEY_COMPONENT_ID in model_definition:
                # The defined model is only one system
                system_id = model_definition[KEY_COMPONENT_ID]
                sub_component = OpenMDAOSystemRegistry.get_system(system_id)
                model.add_subsystem("system", sub_component, promotes=["*"])
            else:
                # The defined model is a group
                self._parse_problem_table(model, model_definition)

        except FASTConfigurationBaseKeyBuildingError as err:
            log_err = err.__class__(err, TABLE_MODEL)
            _LOGGER.error(log_err)
            raise log_err

        set_all_input_defaults(model)
        return model

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

    def _add_constraints(self, model, auto_scaling):
        """
        Adds constraints to provided model as instructed in current configuration

        :param model:
        :param auto_scaling:
        :return:
        """
        optimization_definition = self.get_optimization_definition()
        # Constraints
        constraint_tables = optimization_definition.get(TABLES_CONSTRAINT, {})
        for constraint_table in constraint_tables.values():
            if (
                auto_scaling
                and "lower" in constraint_table
                and "upper" in constraint_table
                and constraint_table.get("ref0") is not None
                and constraint_table.get("ref") is not None
                and constraint_table["lower"] != constraint_table["upper"]
            ):
                constraint_table["ref0"] = constraint_table["lower"]
                constraint_table["ref"] = constraint_table["upper"]
            model.add_constraint(**constraint_table)

    def _add_objectives(self, model):
        """
        Adds objectives to provided model as instructed in current configuration

        :param model:
        :return:
        """
        optimization_definition = self.get_optimization_definition()
        objective_tables = optimization_definition.get(TABLES_OBJECTIVE, {})
        for objective_table in objective_tables.values():
            model.add_objective(**objective_table)

    def _add_design_vars(self, model, auto_scaling):
        """
        Adds design variables to provided model as instructed in current configuration

        :param model:
        :param auto_scaling:
        :return:
        """
        optimization_definition = self.get_optimization_definition()
        design_var_tables = optimization_definition.get(TABLES_DESIGN_VAR, {})
        for design_var_table in design_var_tables.values():
            if (
                auto_scaling
                and "lower" in design_var_table
                and "upper" in design_var_table
                and design_var_table.get("ref0") is not None
                and design_var_table.get("ref") is not None
                and design_var_table["lower"] != design_var_table["upper"]
            ):
                design_var_table["ref0"] = design_var_table["lower"]
                design_var_table["ref"] = design_var_table["upper"]
            model.add_design_var(**design_var_table)


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
