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
import shutil
import sys
from abc import ABC, abstractmethod
from importlib import import_module
from os import PathLike
from pathlib import Path
from typing import Dict, List, Optional, Union

import openmdao.api as om
import tomlkit
from jsonschema import validate
from ruamel.yaml import YAML

from fastoad._utils.files import as_path, make_parent_dir
from fastoad._utils.resource_management.contents import PackageReader
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
KEY_IMPORTS = "imports"
KEY_SYSPATH = "sys.path"
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

        # for storing imported classes
        self._imported_classes = {}

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
            self._configure_driver(problem)

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
        with PackageReader(resources).open_text(JSON_SCHEMA_NAME) as json_file:
            json_schema = json.loads(json_file.read())
        validate(self._data, json_schema)

        # Handle imports
        imports = self._data.get(KEY_IMPORTS, {})
        for module_name, class_name in imports.items():
            if module_name == KEY_SYSPATH:
                # Special case, sys.path is extended.
                # `class_name` is here a list of paths
                folder_list = class_name
                sys.path.extend(folder_list)
            else:
                try:
                    module = import_module(module_name)
                    self._imported_classes[class_name] = getattr(module, class_name)
                except (ImportError, AttributeError) as e:
                    raise ImportError(
                        f"Failed to import {class_name} from {module_name} in configuration file."
                    ) from e

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
        else:
            self._conf_file_path = filename

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

    def make_local(self, new_folder_path: Union[str, PathLike], copy_models: bool = False):
        """
        Modify the current configurator so that all input and output files will be in
        the indicated folder.

        :param new_folder_path: the folder path that will contain in/out files
        :param copy_models: True if local models (declared in `module_folders`) should
                            be copied in `new_folder_path`
        """
        new_folder_path = as_path(new_folder_path)

        self._data[KEY_INPUT_FILE] = self._make_path_local(self.input_file_path, new_folder_path)
        self._data[KEY_OUTPUT_FILE] = self._make_path_local(self.output_file_path, new_folder_path)
        if copy_models:
            new_model_folders = []
            for i, module_folder_path in enumerate(self._get_module_folder_paths()):
                if module_folder_path.is_dir():
                    new_model_folders.append(
                        self._make_path_local(
                            module_folder_path, new_folder_path, local_path=f"models_{i}"
                        )
                    )
            self._data[KEY_FOLDERS] = new_model_folders
        else:
            # Make model folder paths absolutes, since configuration file will be moved.
            # _get_module_folder_paths() already does the job when the configuration file
            # is at its original location.
            self._data[KEY_FOLDERS] = [
                module_folder_path.as_posix()
                for module_folder_path in self._get_module_folder_paths()
            ]

        self._make_options_local(self._data[KEY_MODEL], new_folder_path)
        if KEY_MODEL_OPTIONS in self._data:
            self._make_options_local(
                self._data[KEY_MODEL_OPTIONS], new_folder_path, local_path=Path("model_options")
            )
        self.save(new_folder_path.joinpath(self._conf_file_path.name))

    def _make_options_local(
        self,
        structure: dict,
        new_root_path: Path,
        local_path: Path = Path("."),
    ):
        """
        Recursively modifies `structure` to make each path-like value local with respect to
        `new_root_path`: the value is replaced by `local_path` / <file_name> and if a matching
        file already exists, it is copied in `new_root_path` / `local_path` / <file_name>.

        `local_path` is incremented while the structure is browsed, e.g., with
        `local_path`== "./initial_path" and
        structure["group_1"]["model_2"]["input_file"] == "/any/path/to/foo.txt",
         it will be modified to
         structure["group_1"]["model_2"]["input_file"] == "./initial_path/group_1/model_2/foo.txt".

        Wildcards, that could be encountered in 'model_options', are removed,
        e.g., with `local_path`== ".", result will be:
        structure["model_options"]["loop?.*"]["input_file"] == "./model_options/loop./foo.txt".

        :param structure:
        :param new_root_path:
        :param local_path:
        """
        for key, value in structure.items():
            if isinstance(value, dict) and key != KEY_CONNECTION_ID:
                # wildcards, that could be encountered in 'model_options', are removed.
                new_local_path = local_path / key.replace("*", "").replace("?", "")
                self._make_options_local(value, new_root_path, local_path=new_local_path)
            if key == KEY_COMPONENT_ID or not isinstance(value, str):
                continue

            option_value_as_path = Path(value)
            if not option_value_as_path.is_absolute():
                original_file_path = self._conf_file_path.parent.joinpath(
                    option_value_as_path
                ).resolve()
                if (
                    original_file_path.exists()
                    or len(option_value_as_path.parts) > 1
                    or key.endswith(("file", "path", "dir", "directory", "folder"))
                ):
                    structure[key] = self._make_path_local(
                        original_file_path, new_root_path, local_path / key
                    )

    def _configure_driver(self, prob):
        driver_config = self._data.get(KEY_DRIVER, {})

        # Check if driver_config is a string (old syntax)
        if isinstance(driver_config, str):
            driver_instance_str = driver_config
            prob.driver = self._om_eval(driver_instance_str)
        else:
            # Use new syntax
            # Set the driver instance
            driver_instance = driver_config.get("instance")
            if driver_instance:
                driver_instance = self._om_eval(driver_instance)
                prob.driver = driver_instance

            # Iterate over all keys (attributes) in driver_config except for 'instance'
            for key, value in driver_config.items():
                if key != "instance":
                    getattr(prob.driver, key).update(value)

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

    @staticmethod
    def _make_path_local(
        original_path: Union[str, PathLike],
        new_folder_path: Union[str, PathLike],
        local_path: Optional[Union[str, PathLike]] = None,
    ) -> str:
        """
        For 'original_path' "/foo/bar/baz[.ext]", returns "./baz[.ext]" or
        "./local/path/baz[.ext]" if 'local_path' is "local/path".

        If 'original_path' exists, the file or folder is copied in the
        returned path, relatively to 'new_folder_path'.

        :param original_path:
        :param new_folder_path:
        :param local_path:
        :return: the relative path
        """
        original_path = as_path(original_path)
        new_path = as_path(new_folder_path)
        if local_path:
            new_path /= local_path
        new_path.mkdir(parents=True, exist_ok=True)
        new_path /= original_path.name
        if original_path.is_file():
            shutil.copy(original_path, new_path)
        if original_path.is_dir():
            shutil.copytree(original_path, new_path, dirs_exist_ok=True)
        new_relative_path = new_path.relative_to(new_folder_path).as_posix()
        return new_relative_path

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
                        value = self._om_eval(str(value))
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

    def _om_eval(self, string_to_eval: str):
        """
        Evaluates strings that assume `import openmdao.api as om` is done.
        Evaluates also imports specified in the imports section of the configuration file (if any).

        eval() is used for that, as safely as possible.

        :param string_to_eval:
        :return: result of eval()
        """
        if "__" in string_to_eval:
            raise ValueError(
                "No double underscore allowed in evaluated string for security reasons"
            )
        return eval(string_to_eval, {"__builtins__": {}}, {"om": om, **self._imported_classes})


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
