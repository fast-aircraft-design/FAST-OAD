#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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
import os
import warnings
from copy import deepcopy
from typing import Tuple

import numpy as np
import openmdao
import openmdao.api as om
from openmdao.core.constants import _SetupStatus
from openmdao.core.system import _MetadataDict
from packaging import version

from fastoad.io import DataFile, VariableIO
from fastoad.module_management.service_registry import RegisterSubmodel
from fastoad.openmdao.validity_checker import ValidityDomainChecker
from fastoad.openmdao.variables import VariableList
from ._utils import problem_without_mpi
from .exceptions import FASTOpenMDAONanInInputFile
from ..module_management._bundle_loader import BundleLoader

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
        if (
            version.parse(openmdao.__version__) >= version.parse("3.17")
            and "OPENMDAO_REPORTS" not in os.environ
            and "reports" not in kwargs
            and len(args) < 5
        ):
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
        with problem_without_mpi(self) as problem_copy:
            try:
                super(FASTOADProblem, problem_copy).setup(*args, **kwargs)
            except RuntimeError:
                vars_metadata = self._get_undetermined_dynamic_vars_metadata(problem_copy)
                if vars_metadata:
                    # If vars_metadata is empty, it means the RuntimeError was not because
                    # of dynamic shapes, and the incoming self.setup() will raise it.
                    ivc = om.IndepVarComp()
                    for name, meta in vars_metadata.items():
                        # We use a (2,)-shaped array as value here. This way, it will be easier
                        # to identify dynamic-shaped data in an input file generated from current
                        # problem.
                        ivc.add_output(name, [np.nan, np.nan], units=meta["units"])
                    self.model.add_subsystem(SHAPER_SYSTEM_NAME, ivc, promotes=["*"])

        super().setup(*args, **kwargs)

        if self._read_inputs_after_setup:
            self._read_inputs_with_setup_done()
        BundleLoader().clean_memory()

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

    def _get_problem_inputs(self) -> Tuple[VariableList, VariableList]:
        """
        Reads input file for the configured problem.

        Needed variables and unused variables are
        returned as a VariableList instance.

        :return: VariableList of needed input variables, VariableList with unused variables.
        """

        problem_variables = VariableList().from_problem(self)
        problem_inputs_names = [var.name for var in problem_variables if var.is_input]

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
        with problem_without_mpi(self):
            tmp_prob = deepcopy(self)
            tmp_prob.setup()
            # At this point, there may be non-fed dynamically shaped inputs, so the setup may
            # create the "shaper" IVC, but we ignore it because we need to redefine these variables
            # in input file.
            ivc_vars = tmp_prob.model.get_io_metadata(
                "output",
                tags=["indep_var", "openmdao:indep_var"],
                excludes=f"{SHAPER_SYSTEM_NAME}.*",
            )
        for meta in ivc_vars.values():
            try:
                del input_variables[meta["prom_name"]]
            except ValueError:
                pass
        if input_variables:
            self._insert_input_ivc(input_variables.to_ivc())

    def _insert_input_ivc(self, ivc: om.IndepVarComp, subsystem_name=INPUT_SYSTEM_NAME):
        with problem_without_mpi(self) as tmp_prob:
            tmp_prob.setup()

            # We get order from copied problem, but we have to ignore the "shaper"
            # and the auto IVCs.
            previous_order = [
                system.name
                for system in tmp_prob.model.system_iter(recurse=False)
                if system.name != "_auto_ivc" and system.name != SHAPER_SYSTEM_NAME
            ]

        self.model.add_subsystem(subsystem_name, ivc, promotes=["*"])
        self.model.set_order([subsystem_name] + previous_order)

    @classmethod
    def _get_undetermined_dynamic_vars_metadata(cls, problem):
        """
        Provides dict (name, metadata) for dynamically shaped inputs that are not
        fed by an existing output (assuming overall variable promotion).

        Assumes problem.setup() has been run, at least partially.

        :param problem:
        """
        # First all outputs are identified. If a dynamically shaped input is fed by a matching
        # output, its shaped will be determined.
        output_var_names = []
        for system in problem.model.system_iter(recurse=False):
            io_metadata = cls._get_io_metadata(system, "output")
            output_var_names += [meta["prom_name"] for meta in io_metadata.values()]

        dynamic_vars = {}
        for system in problem.model.system_iter(recurse=False):
            io_metadata = cls._get_io_metadata(system, "input")
            dynamic_vars.update(
                {
                    meta["prom_name"]: meta
                    for name, meta in io_metadata.items()
                    if meta["shape_by_conn"] and meta["prom_name"] not in output_var_names
                }
            )
        return dynamic_vars

    @staticmethod
    def _get_io_metadata(
        system,
        iotypes,
    ):
        # In OpenMDAO >3.16, get_io_metadata() won't complain after dynamically shaped, non-
        # connected inputs.
        if version.parse(openmdao.__version__) >= version.parse("3.17"):
            return system.get_io_metadata(iotypes)

        # For OpenMDAO<=3.16, we try the vanilla get_io_metadata() and if it fails, we
        # try with our simplified implementation.
        try:
            return system.get_io_metadata(iotypes)
        except RuntimeError:
            prefix = system.pathname + "." if system.pathname else ""
            rel_idx = len(prefix)
            if isinstance(iotypes, str):
                iotypes = (iotypes,)

            result = {}
            for iotype in iotypes:
                for abs_name, prom in system._var_abs2prom[iotype].items():
                    rel_name = abs_name[rel_idx:]
                    meta = system._var_allprocs_abs2meta[iotype].get(abs_name)
                    ret_meta = _MetadataDict(meta) if meta is not None else None
                    if ret_meta is not None:
                        ret_meta["prom_name"] = prom
                        result[rel_name] = ret_meta

            warnings.warn(
                "Dynamically shaped problem inputs are better managed with OpenMDAO>3.16 "
                "Upgrade is recommended.",
                DeprecationWarning,
            )
            return result


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
