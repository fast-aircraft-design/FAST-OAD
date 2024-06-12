"""
Module for building OpenMDAO problem from configuration file
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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

import json
import logging
from abc import ABC, abstractmethod
from importlib.resources import open_text
from os import PathLike
from pathlib import Path
from typing import Dict, List, Optional, Union

import openmdao.api as om
import tomlkit
from jsonschema import validate
from ruamel.yaml import YAML

from fastoad._utils.files import as_path, make_parent_dir
from fastoad.io import IVariableIOFormatter
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem, RegisterSubmodel
from fastoad.openmdao.problem import FASTOADProblem
from . import resources
from .exceptions import (
    FASTConfigurationBadOpenMDAOInstructionError,
    FASTConfigurationBaseKeyBuildingError,
)

_LOGGER = logging.getLogger(__name__)  # Logger for this module

KEY_FOLDERS = "module_folders"
KEY_INPUT_FILE = "input_file"
KEY_OUTPUT_FILE = "output_file"
KEY_COMPONENT_ID = "id"
KEY_CONNECTION_ID = "connections"
KEY_MODEL = "model"
KEY_SUBMODELS = "submodels"
KEY_DRIVER = "driver"
KEY_MODEL_OPTIONS = "model_options"
KEY_OPTIMIZATION = "optimization"
KEY_DESIGN_VARIABLES = "design_variables"
KEY_CONSTRAINTS = "constraints"
KEY_OBJECTIVE = "objective"
JSON_SCHEMA_NAME = "configuration.json"


class FASTOADProblemConfigurator:
    """
    class for configuring an OpenMDAO problem from a configuration file

    See :ref:`description of configuration file <configuration-file>`.

    :param conf_file_path: if provided, configuration will be read directly from it
    """

    def __init__(self, conf_file_path: Union[str, PathLike] = None):
        self._serializer: _IDictSerializer = _YAMLSerializer()

        # self._configuration_modifier offers a way to modify problems after
        # they have been generated from configuration (private usage for now)
        self._configuration_modifier: Optional["_IConfigurationModifier"] = None

        self._conf_file_path: Optional[Path] = None
        if conf_file_path:
            self.load(conf_file_path)

    @property
    def input_file_path(self) -> str:
        """path of file with input variables of the problem"""
        return self._make_absolute(self._data[KEY_INPUT_FILE]).as_posix()

    @input_file_path.setter
    def input_file_path(self, file_path: Union[str, PathLike]):
        self._data[KEY_INPUT_FILE] = str(file_path)

    @property
    def output_file_path(self) -> str:
        """path of file where output variables will be written"""
        return self._make_absolute(self._data[KEY_OUTPUT_FILE]).as_posix()

    @output_file_path.setter
    def output_file_path(self, file_path: Union[str, PathLike]):
        self._data[KEY_OUTPUT_FILE] = str(file_path)

    @property
    def _data(self) -> dict:
        return self._serializer.data

    def get_problem(self, read_inputs: bool = False, auto_scaling: bool = False) -> FASTOADProblem:
        """
        Builds the OpenMDAO problem from current configuration.

        :param read_inputs: if True, the created problem will already be fed
                            with variables from the input file
        :param auto_scaling: if True, automatic scaling is performed for design
                             variables and constraints
        :return: the problem instance
        """
        if self._data is None:
            raise RuntimeError("read configuration file first")

        problem = FASTOADProblem()
        self._build_model(problem)

        if self._configuration_modifier:
            self._configuration_modifier.modify(problem)

        problem.input_file_path = self.input_file_path
        problem.output_file_path = self.output_file_path

        model_options = self._data.get(KEY_MODEL_OPTIONS, {})
        for options in model_options.values():
            self._make_option_path_values_absolute(options)
        problem.model_options = model_options

        if read_inputs:
            problem.read_inputs()

        driver = self._data.get(KEY_DRIVER, "")
        if driver:
            problem.driver = _om_eval(driver)

        if self.get_optimization_definition():
            self._add_constraints(problem.model, auto_scaling)
            self._add_objectives(problem.model)

        if read_inputs:
            self._add_design_vars(problem.model, auto_scaling)

        return problem

    def load(self, conf_file: Union[str, PathLike]):
        """
        Reads the problem definition

        :param conf_file: Path to the file to open
        """

        self._conf_file_path = as_path(conf_file).resolve()  # for resolving relative paths

        if self._conf_file_path.suffix == ".toml":
            self._serializer = _TOMLSerializer()
            _LOGGER.warning(
                "TOML-formatted configuration files are deprecated. Please use YAML format."
            )
        else:
            self._serializer = _YAMLSerializer()
        self._serializer.read(self._conf_file_path)

        # Syntax validation
        with open_text(resources, JSON_SCHEMA_NAME) as json_file:
            json_schema = json.loads(json_file.read())
        validate(self._data, json_schema)

        # Issue a simple warning for unknown keys at root level
        for key in self._data:
            if key not in json_schema["properties"].keys():
                _LOGGER.warning('Configuration file: "%s" is not a FAST-OAD key.', key)

        # Looking for modules to register
        for module_folder_path in self._get_module_folder_paths():
            if not module_folder_path.is_dir():
                _LOGGER.warning("SKIPPED %s: it does not exist.", module_folder_path)
            else:
                RegisterOpenMDAOSystem.explore_folder(module_folder_path.as_posix())

        # Settings submodels
        RegisterSubmodel.cancel_submodel_deactivations()
        submodel_specs = self._data.get(KEY_SUBMODELS, {})
        for submodel_requirement, submodel_id in submodel_specs.items():
            RegisterSubmodel.active_models[submodel_requirement] = submodel_id

    def save(self, filename: Union[str, PathLike] = None):
        """
        Saves the current configuration
        If no filename is provided, the initially read file is used.

        :param filename: file where to save configuration
        """
        if not filename:
            filename = self._conf_file_path

        make_parent_dir(filename)
        self._serializer.write(filename)

    def write_needed_inputs(
        self,
        source_file_path: Union[str, PathLike] = None,
        source_formatter: IVariableIOFormatter = None,
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
        conf_dict = self._data.get(KEY_OPTIMIZATION)
        if conf_dict:
            for sec, elements in conf_dict.items():
                optimization_definition[sec] = {elem["name"]: elem for elem in elements}
        return optimization_definition

    def set_optimization_definition(self, optimization_definition: Dict):
        """
        Updates configuration with the list of design variables, constraints, objectives
        contained in the optimization_definition dictionary.

        Keys of the dictionary are: "design_var", "constraint", "objective".

        Configuration file will not be modified until :meth:`save` is used.

        :param optimization_definition: dict containing the optimization problem definition
        """
        subpart = {}
        for key, value in optimization_definition.items():
            subpart[key] = [value for _, value in optimization_definition[key].items()]
        subpart = {"optimization": subpart}
        self._data.update(subpart)

    def _make_absolute(self, path: Union[str, PathLike]) -> Path:
        """
        Make the provided path absolute using configuration file folder as base.

        Does nothing if the path is already absolute.
        """
        path = as_path(path)
        if not path.is_absolute():
            path = (self._conf_file_path.parent / path).resolve()
        return path

    def _get_module_folder_paths(self) -> List[Path]:
        module_folder_paths = self._data.get(KEY_FOLDERS)
        # Key may be present, but with None value
        if not module_folder_paths:
            return []
        if isinstance(module_folder_paths, str):
            module_folder_paths = [module_folder_paths]
        return [self._make_absolute(folder_path) for folder_path in module_folder_paths]

    def _build_model(self, problem: FASTOADProblem):
        """
        Builds the problem model as defined in the configuration file.

        The problem model is populated with subsystems indicated in configuration file.
        """

        model = problem.model
        model.active_submodels = self._data.get(KEY_SUBMODELS, {})

        model_definition = self._data.get(KEY_MODEL)

        try:
            if KEY_COMPONENT_ID in model_definition:
                # The defined model is only one system
                system_id = model_definition[KEY_COMPONENT_ID]
                sub_component = RegisterOpenMDAOSystem.get_system(system_id)
                model.add_subsystem("system", sub_component, promotes=["*"])
            else:
                # The defined model is a group
                self._parse_problem_table(model, model_definition)

        except FASTConfigurationBaseKeyBuildingError as err:
            log_err = err.__class__(err, KEY_MODEL)
            _LOGGER.error(log_err)
            raise log_err

    def _parse_problem_table(self, group: om.Group, table: dict):
        """
        Feeds provided *group*, using definition in provided TOML *table*.

        :param group:
        :param table:
        """
        # assert isinstance(table, dict), "table should be a dictionary"

        for key, value in table.items():
            if isinstance(value, dict):  # value defines a sub-component
                if KEY_COMPONENT_ID in value:
                    # It is a non-group component, that should be registered with its ID
                    options = value.copy()
                    identifier = options.pop(KEY_COMPONENT_ID)

                    self._make_option_path_values_absolute(options)

                    sub_component = RegisterOpenMDAOSystem.get_system(identifier, options=options)
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
            elif key == KEY_CONNECTION_ID and isinstance(value, list):
                # a list of dict currently defines only connections
                for connection_def in value:
                    group.connect(connection_def["source"], connection_def["target"])
            else:
                # value may have to be literally interpreted
                if key.endswith(("solver", "driver")):
                    try:
                        value = _om_eval(str(value))
                    except Exception as err:
                        raise FASTConfigurationBadOpenMDAOInstructionError(err, key, value)

                # value is an option or an attribute
                try:
                    if key in group.options:
                        group.options[key] = value
                    else:
                        setattr(group, key, value)
                except Exception as err:
                    raise FASTConfigurationBadOpenMDAOInstructionError(err, key, value)

    def _make_option_path_values_absolute(self, options):
        # Process option values that are relative paths
        conf_folder_path = self._conf_file_path.parent
        for name, option_value in options.items():
            if (
                isinstance(option_value, str)
                and name.endswith(("file", "path", "dir", "directory", "folder"))
                and not Path(option_value).is_absolute()
            ):
                options[name] = (conf_folder_path / option_value).as_posix()

    def _add_constraints(self, model, auto_scaling):
        """
        Adds constraints to provided model as instructed in current configuration

        :param model:
        :param auto_scaling:
        :return:
        """
        optimization_definition = self.get_optimization_definition()
        # Constraints
        constraint_tables = optimization_definition.get(KEY_CONSTRAINTS, {})
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
        objective_tables = optimization_definition.get(KEY_OBJECTIVE, {})
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
        design_var_tables = optimization_definition.get(KEY_DESIGN_VARIABLES, {})
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

    def _set_configuration_modifier(self, modifier: "_IConfigurationModifier"):
        self._configuration_modifier = modifier


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


class _IDictSerializer(ABC):
    """Interface for reading and writing dict-like data"""

    @property
    @abstractmethod
    def data(self) -> dict:
        """
        The data that have been read, or will be written.
        """

    @abstractmethod
    def read(self, file_path: Union[str, PathLike]):
        """
        Reads data from provided file.
        :param file_path:
        """

    @abstractmethod
    def write(self, file_path: Union[str, PathLike]):
        """
        Writes data to provided file.
        :param file_path:
        """


class _TOMLSerializer(_IDictSerializer):
    """TOML-format serializer."""

    def __init__(self):
        self._data = None

    @property
    def data(self):
        return self._data

    def read(self, file_path: Union[str, PathLike]):
        with open(file_path, "r") as toml_file:
            self._data = tomlkit.loads(toml_file.read()).value

    def write(self, file_path: Union[str, PathLike]):
        with open(file_path, "w") as file:
            file.write(tomlkit.dumps(self._data))


class _YAMLSerializer(_IDictSerializer):
    """YAML-format serializer."""

    def __init__(self):
        self._data = None

    @property
    def data(self):
        return self._data

    def read(self, file_path: Union[str, PathLike]):
        yaml = YAML(typ="safe")
        with open(file_path) as yaml_file:
            self._data = yaml.load(yaml_file)

    def write(self, file_path: Union[str, PathLike]):
        yaml = YAML()
        yaml.default_flow_style = False
        with open(file_path, "w") as file:
            yaml.dump(self._data, file)


class _IConfigurationModifier(ABC):
    """
    Interface for a configuration modifier used in FASTOADProblemConfigurator.
    """

    @abstractmethod
    def modify(self, problem: om.Problem):
        """
        This method will do operations on the provided problem.

        problem.setup() is assumed NOT called.
        """
