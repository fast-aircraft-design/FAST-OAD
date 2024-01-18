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

import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np
import openmdao.api as om
from openmdao.core.constants import _SetupStatus
from openmdao.core.system import System

from fastoad.io import DataFile, IVariableIOFormatter, VariableIO
from fastoad.module_management.service_registry import RegisterSubmodel
from fastoad.openmdao.validity_checker import ValidityDomainChecker
from fastoad.openmdao.variables import Variable, VariableList
from ._utils import get_mpi_safe_problem_copy
from .exceptions import FASTOpenMDAONanInInputFile
from ..module_management._bundle_loader import BundleLoader

_LOGGER = logging.getLogger(__name__)  # Logger for this module

# Name of IVC that will contain input values
INPUT_SYSTEM_NAME = "fastoad_inputs"

# Name of IVC that will temporarily set shapes for dynamically shaped inputs
SHAPER_SYSTEM_NAME = "fastoad_shaper"


class FASTOADProblem(om.Problem):
    """
    Vanilla OpenMDAO Problem except that it can write its outputs to a file.

    It also runs :class:`~fastoad.openmdao.validity_checker.ValidityDomainChecker`
    after each :meth:`run_model` or :meth:`run_driver`
    (but it does nothing if no check has been registered).
    """

    def __init__(self, *args, **kwargs):
        # Automatic reports are deactivated for FAST-OAD, unless OPENMDAO_REPORTS env
        # variable is set.
        kwargs["reports"] = None
        super().__init__(*args, **kwargs)

        #: File path where :meth:`read_inputs` will read inputs
        self.input_file_path = None
        #: File path where :meth:`write_outputs` will write outputs
        self.output_file_path = None

        #: Variables that are not part of the problem but that should be written in output file.
        self.additional_variables = None

        #: If True inputs will be read after setup.
        self._read_inputs_after_setup = False

        self.model = FASTOADModel()

        self._copy = None

        self._analysis: Optional[ProblemAnalysis] = None

    def run_model(self, case_prefix=None, reset_iter_counts=True):
        status = super().run_model(case_prefix, reset_iter_counts)
        ValidityDomainChecker.check_problem_variables(self)
        BundleLoader().clean_memory()
        return status

    def run_driver(self, case_prefix=None, reset_iter_counts=True):
        status = super().run_driver(case_prefix, reset_iter_counts)
        ValidityDomainChecker.check_problem_variables(self)
        BundleLoader().clean_memory()
        return status

    def setup(self, *args, **kwargs):
        """
        Set up the problem before run.
        """
        self.analysis.fills_dynamically_shaped_inputs(self)

        super().setup(*args, **kwargs)

        if self._read_inputs_after_setup:
            self._read_inputs_with_setup_done()
        BundleLoader().clean_memory()

    def write_needed_inputs(
        self, source_file_path: str = None, source_formatter: IVariableIOFormatter = None
    ):
        """
        Writes the input file of the problem using its unconnected inputs.

        Written value of each variable will be taken:

            1. from input_data if it contains the variable
            2. from defined default values in component definitions

        :param source_file_path: if provided, variable values will be read from it
        :param source_formatter: the class that defines format of input file. if
                                 not provided, expected format will be the default one.
        """
        variables = DataFile(self.input_file_path, load_data=False)

        unconnected_inputs = VariableList(
            [variable for variable in self.analysis.problem_variables if variable.is_input]
        )

        variables.update(
            unconnected_inputs,
            add_variables=True,
        )
        if source_file_path:
            ref_vars = DataFile(source_file_path, formatter=source_formatter)
            variables.update(ref_vars, add_variables=False)
            nan_variable_names = []
            for var in variables:
                var.is_input = True
                # Checking if variables have NaN values
                if np.any(np.isnan(var.value)):
                    nan_variable_names.append(var.name)
            if nan_variable_names:
                _LOGGER.warning("The following variables have NaN values: %s", nan_variable_names)
        variables.save()

    def write_outputs(self):
        """
        Writes all outputs in the configured output file.
        """
        if self.output_file_path:
            writer = VariableIO(self.output_file_path)

            if self.additional_variables is None:
                self.additional_variables = []
            variables = VariableList(self.additional_variables)
            for var in variables:
                var.is_input = None
            variables.update(
                VariableList.from_problem(self, promoted_only=True), add_variables=True
            )
            writer.write(variables)

    def read_inputs(self):
        """
        Reads inputs of the problem.
        """
        if self._metadata and self._metadata["setup_status"] == _SetupStatus.POST_SETUP:
            self._read_inputs_with_setup_done()
        else:
            self._read_inputs_without_setup_done()
            # Input reading still needs to be done after setup, to ensure that IVC values
            # will be properly set by new inputs.
            self._read_inputs_after_setup = True

    @property
    def analysis(self) -> "ProblemAnalysis":
        """
        Information about inner structure of this problem.

        The collected data (internally stored) are used in several steps of the computation.

        This analysis is performed once. Each subsequent usage reuses the obtained data.

        To ensure the analysis is run again, use :meth:`reset_analysis`.
        """
        if self._analysis is None:
            self._analysis = ProblemAnalysis(self)

        return self._analysis

    def reset_analysis(self):
        """
        Ensure a new problem analysis is done at new usage of :attr:`analysis`.
        """
        self._analysis = None

    def _get_problem_inputs(self) -> Tuple[VariableList, VariableList]:
        """
        Reads input file for the configured problem.

        Needed variables and unused variables are
        returned as a VariableList instance.

        :return: VariableList of needed input variables, VariableList with unused variables.
        """
        problem_inputs_names = [var.name for var in self.analysis.problem_variables if var.is_input]

        input_variables = DataFile(self.input_file_path)

        unused_variables = VariableList(
            [var for var in input_variables if var.name not in problem_inputs_names]
        )
        for name in unused_variables.names():
            del input_variables[name]

        nan_variable_names = [var.name for var in input_variables if np.any(np.isnan(var.value))]
        if nan_variable_names:
            raise FASTOpenMDAONanInInputFile(self.input_file_path, nan_variable_names)

        return input_variables, unused_variables

    def _read_inputs_with_setup_done(self):
        """
        Set initial values of inputs. self.setup() must have been run.
        """
        input_variables, unused_variables = self._get_problem_inputs()
        self.additional_variables = unused_variables
        for input_var in input_variables:
            # set_val() will crash if input_var.metadata["val"] is a list, so
            # we ensure it is a numpy array
            input_var.metadata["val"] = np.asarray(input_var.metadata["val"])

            self.set_val(input_var.name, val=input_var.val, units=input_var.units)

    def _read_inputs_without_setup_done(self):
        """
        Set initial values of inputs. self.setup() must have NOT been run.

        Input values that match an existing IVC are not taken into account
        """
        input_variables, unused_variables = self._get_problem_inputs()
        self.additional_variables = unused_variables

        input_variables = VariableList(
            [
                variable
                for variable in input_variables
                if variable.name not in self.analysis.ivc_var_names
            ]
        )

        if input_variables:
            self.analysis.dynamic_input_vars = VariableList(
                [
                    variable
                    for variable in self.analysis.dynamic_input_vars
                    if variable.name not in input_variables.names()
                ]
            )
            self._insert_input_ivc(input_variables.to_ivc())

    def _insert_input_ivc(self, ivc: om.IndepVarComp, subsystem_name=INPUT_SYSTEM_NAME):
        self.model.add_subsystem(subsystem_name, ivc, promotes=["*"])
        self.model.set_order([subsystem_name] + self.analysis.subsystem_order)


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


def get_variable_list_from_system(
    system: System,
    get_promoted_names: bool = True,
    promoted_only: bool = True,
    io_status: str = "all",
) -> "VariableList":
    """
    Creates a VariableList instance containing inputs and outputs of any OpenMDAO System.

    Convenience method that creates a FASTOADProblem problem with only provided `system`
    and uses :meth:`~fastoad.openmdao.variables.variable.VariableList.from_problem()`.
    """
    # Dev note:
    # This method is not a class method of VariableList because it would
    # create a circular import because of the usage of FASTOADProblem.
    # And usage of FASTOADProblem instead of om.Problem avoids failure in case
    # there are shape_by_conn inputs.
    problem = FASTOADProblem()
    problem.model.add_subsystem("comp", system, promotes=["*"])
    return VariableList.from_problem(
        problem,
        get_promoted_names=get_promoted_names,
        promoted_only=promoted_only,
        io_status=io_status,
    )


@dataclass
class ProblemAnalysis:
    """Class for retrieving information about the input OpenMDAO problem.

    At least one setup operation is done on a copy of the problem.
    Two setup operations will be done if the problem has unfed dynamically
    shaped inputs.
    """

    #: The analyzed problem
    problem: om.Problem

    #: All variables of the problem
    problem_variables: VariableList = field(default_factory=VariableList, init=False)

    #: List variables that are inputs OF THE PROBLEM and dynamically shaped.
    dynamic_input_vars: VariableList = field(default_factory=VariableList, init=False)

    #: Order of subsystems
    subsystem_order: list = field(default_factory=list, init=False)

    #: Names of variables that are output of an IndepVarComp
    ivc_var_names: list = field(default_factory=list, init=False)

    def __post_init__(self):
        self.analyze()

    def analyze(self):
        """
        Gets information about inner structure of the associated problem.
        """
        problem_copy = get_mpi_safe_problem_copy(self.problem)
        try:
            om.Problem.setup(problem_copy)
        except RuntimeError:
            self.dynamic_input_vars = self._get_undetermined_dynamic_vars(problem_copy)

            problem_copy = get_mpi_safe_problem_copy(self.problem)
            self.fills_dynamically_shaped_inputs(problem_copy)
            om.Problem.setup(problem_copy)

        self.problem_variables = VariableList().from_problem(problem_copy)

        self.ivc_var_names = [
            meta["prom_name"]
            for meta in problem_copy.model.get_io_metadata(
                "output",
                tags=["indep_var", "openmdao:indep_var"],
                excludes=f"{SHAPER_SYSTEM_NAME}.*",
            ).values()
        ]

        self.subsystem_order = self._get_order_of_subsystems(problem_copy)

    def fills_dynamically_shaped_inputs(self, problem: om.Problem):
        """
        Adds to the problem an IndepVarComp, that provides dummy variables to fit the
        dynamically shaped inputs of the analyzed problem.

        Adding this IVC to the problem will allow to complete the setup operation.

        The input problem should be the analyzed problem or a copy of it.
        """
        if self.dynamic_input_vars:
            # If vars_metadata is empty, it means the RuntimeError was not because
            # of dynamic shapes, and the incoming self.setup() will raise it.
            ivc = om.IndepVarComp()
            for variable in self.dynamic_input_vars:
                # We use a (2,)-shaped array as value here. This way, it will be easier
                # to identify dynamic-shaped data in an input file generated from current
                # problem.
                ivc.add_output(variable.name, [np.nan, np.nan], units=variable.units)
            problem.model.add_subsystem(SHAPER_SYSTEM_NAME, ivc, promotes=["*"])

    @staticmethod
    def _get_undetermined_dynamic_vars(problem) -> VariableList:
        """
        Provides variable list of dynamically shaped inputs that are not
        fed by an existing output (assuming overall variable promotion).

        Assumes problem.setup() has been run, at least partially.

        :param problem:
        :return: the variable list
        """
        # First all outputs are identified. If a dynamically shaped input is fed by a matching
        # output, its shaped will be determined.
        output_var_names = []
        for system in problem.model.system_iter(recurse=False):
            io_metadata = system.get_io_metadata("output")
            output_var_names += [meta["prom_name"] for meta in io_metadata.values()]

        dynamic_vars_metadata = {}
        for system in problem.model.system_iter(recurse=False):
            io_metadata = system.get_io_metadata("input")
            dynamic_vars_metadata.update(
                {
                    meta["prom_name"]: meta
                    for name, meta in io_metadata.items()
                    if meta["shape_by_conn"] and meta["prom_name"] not in output_var_names
                }
            )

        dynamic_vars = VariableList(
            [Variable(meta["prom_name"], **meta) for meta in dynamic_vars_metadata.values()]
        )

        return dynamic_vars

    @staticmethod
    def _get_order_of_subsystems(problem, ignored_system_names=("_auto_ivc", SHAPER_SYSTEM_NAME)):
        return [
            system.name
            for system in problem.model.system_iter(recurse=False)
            if system.name not in ignored_system_names
        ]
