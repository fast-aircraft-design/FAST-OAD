"""
Module for building OpenMDAO problem from configuration file
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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
import os.path as pth
from abc import ABC, abstractmethod
from importlib.resources import open_text
from typing import Dict, Tuple

import numpy as np
import openmdao.api as om
import tomlkit
from jsonschema import validate
from ruamel.yaml import YAML

from fastoad._utils.files import make_parent_dir
from fastoad.io import DataFile, IVariableIOFormatter
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem, RegisterSubmodel
from fastoad.openmdao._utils import get_unconnected_input_names
from fastoad.openmdao.problem import FASTOADProblem
from fastoad.openmdao.variables import VariableList
from . import resources
from .exceptions import (
    FASTConfigurationBadOpenMDAOInstructionError,
    FASTConfigurationBaseKeyBuildingError,
    FASTConfigurationNanInInputFile,
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

    def __init__(self, conf_file_path=None):
        self._conf_file = None

        self._serializer = _YAMLSerializer()

        # self._configuration_modifier offers a way to modify problems after
        # they have been generated from configuration (private usage for now)
        self._configuration_modifier: "_IConfigurationModifier" = None

        if conf_file_path:
            self.load(conf_file_path)

    @property
    def input_file_path(self):
        """path of file with input variables of the problem"""
        path = str(self._serializer.data[KEY_INPUT_FILE])
        if not pth.isabs(path):
            path = pth.normpath(pth.join(pth.dirname(self._conf_file), path))
        return path

    @input_file_path.setter
    def input_file_path(self, file_path: str):
        self._serializer.data[KEY_INPUT_FILE] = file_path

    @property
    def output_file_path(self):
        """path of file where output variables will be written"""
        path = str(self._serializer.data[KEY_OUTPUT_FILE])
        if not pth.isabs(path):
            path = pth.normpath(pth.join(pth.dirname(self._conf_file), path))
        return path

    @output_file_path.setter
    def output_file_path(self, file_path: str):
        self._serializer.data[KEY_OUTPUT_FILE] = file_path

    def get_problem(self, read_inputs: bool = False, auto_scaling: bool = False) -> FASTOADProblem:
        """
        Builds the OpenMDAO problem from current configuration.

        :param read_inputs: if True, the created problem will already be fed
                            with variables from the input file
        :param auto_scaling: if True, automatic scaling is performed for design
                             variables and constraints
        :return: the problem instance
        """
        if self._serializer.data is None:
            raise RuntimeError("read configuration file first")

        if read_inputs:
            problem_with_no_inputs = self.get_problem(auto_scaling=auto_scaling)
            problem_with_no_inputs.setup()
            input_ivc, unused_variables = self._get_problem_inputs(problem_with_no_inputs)
        else:
            input_ivc = unused_variables = None

        problem = FASTOADProblem(self._build_model(input_ivc))
        problem.input_file_path = self.input_file_path
        problem.output_file_path = self.output_file_path
        problem.additional_variables = unused_variables

        driver = self._serializer.data.get(KEY_DRIVER, "")
        if driver:
            problem.driver = _om_eval(driver)

        if self.get_optimization_definition():
            self._add_constraints(problem.model, auto_scaling)
            self._add_objectives(problem.model)

        if read_inputs:
            self._add_design_vars(problem.model, auto_scaling)

        if self._configuration_modifier:
            self._configuration_modifier.modify(problem)

        return problem

    def load(self, conf_file):
        """
        Reads the problem definition

        :param conf_file: Path to the file to open or a file descriptor
        """

        self._conf_file = pth.abspath(conf_file)  # for resolving relative paths
        conf_dirname = pth.dirname(self._conf_file)

        if pth.splitext(self._conf_file)[-1] == ".toml":
            self._serializer = _TOMLSerializer()
            _LOGGER.warning(
                "TOML-formatted configuration files are deprecated. Please use YAML format."
            )
        else:
            self._serializer = _YAMLSerializer()
        self._serializer.read(self._conf_file)

        # Syntax validation
        with open_text(resources, JSON_SCHEMA_NAME) as json_file:
            json_schema = json.loads(json_file.read())
        validate(self._serializer.data, json_schema)
        # Issue a simple warning for unknown keys at root level
        for key in self._serializer.data:
            if key not in json_schema["properties"].keys():
                _LOGGER.warning('Configuration file: "%s" is not a FAST-OAD key.', key)

        # Looking for modules to register
        module_folder_paths = self._serializer.data.get(KEY_FOLDERS)
        if isinstance(module_folder_paths, str):
            module_folder_paths = [module_folder_paths]
        if module_folder_paths:
            for folder_path in module_folder_paths:
                folder_path = pth.join(conf_dirname, str(folder_path))
                if not pth.exists(folder_path):
                    _LOGGER.warning("SKIPPED %s: it does not exist.", folder_path)
                else:
                    RegisterOpenMDAOSystem.explore_folder(folder_path)

        # Settings submodels
        submodel_specs = self._serializer.data.get(KEY_SUBMODELS, {})
        for submodel_requirement, submodel_id in submodel_specs.items():
            RegisterSubmodel.active_models[submodel_requirement] = submodel_id

    def save(self, filename: str = None):
        """
        Saves the current configuration
        If no filename is provided, the initially read file is used.

        :param filename: file where to save configuration
        """
        if not filename:
            filename = self._conf_file

        make_parent_dir(filename)
        self._serializer.write(filename)

    def write_needed_inputs(
        self, source_file_path: str = None, source_formatter: IVariableIOFormatter = None
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
        problem.setup()
        variables = DataFile(self.input_file_path, load_data=False)
        variables.update(
            VariableList.from_unconnected_inputs(problem, with_optional_inputs=True),
            add_variables=True,
        )
        if source_file_path:
            ref_vars = DataFile(source_file_path, formatter=source_formatter)
            variables.update(ref_vars, add_variables=False)
            for var in variables:
                var.is_input = True
        variables.save()

    def get_optimization_definition(self) -> Dict:
        """
        Returns information related to the optimization problem:
            - Design Variables
            - Constraints
            - Objectives

        :return: dict containing optimization settings for current problem
        """

        optimization_definition = {}
        conf_dict = self._serializer.data.get(KEY_OPTIMIZATION)
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
        self._serializer.data.update(subpart)

    def _build_model(self, input_ivc: om.IndepVarComp = None) -> om.Group:
        """
        Builds the model as defined in the configuration file.

        The model is initialized as a new group and populated with subsystems
        indicated in configuration file.

        :return: the built model
        """

        model = FASTOADModel()
        model.active_submodels = self._serializer.data.get(KEY_SUBMODELS, {})

        if input_ivc:
            model.add_subsystem("fastoad_inputs", input_ivc, promotes=["*"])

        model_definition = self._serializer.data.get(KEY_MODEL)

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

        return model

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

                    # Process option values that are relative paths
                    conf_dirname = pth.dirname(self._conf_file)
                    for name, option_value in options.items():
                        option_is_path = (
                            name.endswith("file")
                            or name.endswith("path")
                            or name.endswith("dir")
                            or name.endswith("directory")
                            or name.endswith("folder")
                        )
                        if (
                            isinstance(option_value, str)
                            and option_is_path
                            and not pth.isabs(option_value)
                        ):
                            options[name] = pth.join(conf_dirname, option_value)

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
                # value is an attribute of current component and will be literally interpreted
                try:
                    setattr(group, key, _om_eval(str(value)))  # pylint:disable=eval-used
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

    def _get_problem_inputs(self, problem: FASTOADProblem) -> Tuple[om.IndepVarComp, VariableList]:
        """
        Reads input file for the configure problem.

        Needed variables are returned as an IndepVarComp instance while unused variables are
        returned as a VariableList instance.

        :param problem: problem with missing inputs. setup() must have been run.
        :return: IVC of needed input variables, VariableList with unused variables.
        """
        mandatory, optional = get_unconnected_input_names(problem, promoted_names=True)
        needed_variable_names = mandatory + optional

        input_variables = DataFile(self.input_file_path)

        unused_variables = VariableList(
            [var for var in input_variables if var.name not in needed_variable_names]
        )
        for name in unused_variables.names():
            del input_variables[name]

        nan_variable_names = [var.name for var in input_variables if np.all(np.isnan(var.value))]
        if nan_variable_names:
            raise FASTConfigurationNanInInputFile(self.input_file_path, nan_variable_names)

        input_ivc = input_variables.to_ivc()
        return input_ivc, unused_variables

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


class AutoUnitsDefaultGroup(om.Group):
    """
    OpenMDAO group that automatically use self.set_input_defaults() to resolve declaration
    conflicts in variable units.
    """

    def configure(self):
        var_units = {}
        system: om.Group
        for system in self.system_iter(recurse=False):
            system_metadata = system.get_io_metadata("input", metadata_keys=["units"])
            var_units.update(
                {
                    metadata["prom_name"]: metadata["units"]
                    for name, metadata in system_metadata.items()
                    if "." not in metadata["prom_name"]  # tells that var is promoted
                }
            )
        for name, units in var_units.items():
            self.set_input_defaults(name, units=units)


class FASTOADModel(AutoUnitsDefaultGroup):
    """
    OpenMDAO group that defines active submodels after the initialization
    of all its subsystems, and inherits from :class:`AutoUnitsDefaultGroup` for resolving
    declaration conflicts in variable units.

    It allows to have a submodel choice in the initialize() method of a FAST-OAD module, but
    to possibly override it with the definition of :attr:`active_submodels` (i.e. from the
    configuration file).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #: Definition of active submodels that will be applied during setup()
        self.active_submodels = {}

    def setup(self):
        RegisterSubmodel.active_models.update(self.active_submodels)


class _IDictSerializer(ABC):
    """Interface for reading and writing dict-like data"""

    @property
    @abstractmethod
    def data(self) -> dict:
        """
        The data that have been read, or will be written.
        """

    @abstractmethod
    def read(self, file_path: str):
        """
        Reads data from provided file.
        :param file_path:
        """

    @abstractmethod
    def write(self, file_path: str):
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

    def read(self, file_path: str):
        with open(file_path, "r") as toml_file:
            self._data = tomlkit.loads(toml_file.read())

    def write(self, file_path: str):
        with open(file_path, "w") as file:
            file.write(tomlkit.dumps(self._data))


class _YAMLSerializer(_IDictSerializer):
    """YAML-format serializer."""

    def __init__(self):
        self._data = None

    @property
    def data(self):
        return self._data

    def read(self, file_path: str):
        yaml = YAML(typ="safe")
        with open(file_path) as yaml_file:
            self._data = yaml.load(yaml_file)

    def write(self, file_path: str):
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
