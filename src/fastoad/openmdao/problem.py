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

from copy import deepcopy
from typing import Tuple

import numpy as np
import openmdao.api as om
from openmdao.core.constants import _SetupStatus

from fastoad.io import DataFile, VariableIO
from fastoad.openmdao.exceptions import (
    FASTOpenMDAONanInInputFile,
)
from fastoad.openmdao.validity_checker import ValidityDomainChecker
from fastoad.openmdao.variables import VariableList

INPUT_SYSTEM_NAME = "inputs"


class FASTOADProblem(om.Problem):
    """Vanilla OpenMDAO Problem except that it can write its outputs to a file.

    It also runs :class:`~fastoad.openmdao.validity_checker.ValidityDomainChecker`
    after each :meth:`run_model` or :meth:`run_driver`
    (but it does nothing if no check has been registered).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #: File path where :meth:`read_inputs` will read inputs
        self.input_file_path = None
        #: File path where :meth:`write_outputs` will write outputs
        self.output_file_path = None

        #: Variables that are not part of the problem but that should be written in output file.
        self.additional_variables = None

        #: If True inputs will be read after setup.
        self._read_inputs_after_setup = False

    def run_model(self, case_prefix=None, reset_iter_counts=True):
        status = super().run_model(case_prefix, reset_iter_counts)
        ValidityDomainChecker.check_problem_variables(self)
        return status

    def run_driver(self, case_prefix=None, reset_iter_counts=True):
        status = super().run_driver(case_prefix, reset_iter_counts)
        ValidityDomainChecker.check_problem_variables(self)
        return status

    def setup(self, *args, **kwargs):
        """
        Set up the problem before run.
        """
        super().setup(*args, **kwargs)
        if self._read_inputs_after_setup:
            self._read_inputs_with_setup_done()

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

        nan_variable_names = [var.name for var in input_variables if np.all(np.isnan(var.value))]
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
            self.set_val(input_var.name, **input_var.metadata)

    def _read_inputs_without_setup_done(self):
        """
        Set initial values of inputs. self.setup() must have NOT been run.

        Input values that match an existing IVC are not taken into account
        """
        input_variables, unused_variables = self._get_problem_inputs()
        self.additional_variables = unused_variables
        tmp_prob = deepcopy(self)
        tmp_prob.setup()
        ivc_vars = tmp_prob.model.get_io_metadata("output", tags="indep_var")
        for meta in ivc_vars.values():
            try:
                del input_variables[meta["prom_name"]]
            except ValueError:
                pass
        if input_variables:
            self._insert_input_ivc(input_variables.to_ivc())

    def _insert_input_ivc(self, ivc: om.IndepVarComp, subsystem_name="fastoad_inputs"):
        tmp_prob = deepcopy(self)
        tmp_prob.setup()

        previous_order = [
            system.name
            for system in tmp_prob.model.system_iter(recurse=False)
            if system.name != "_auto_ivc"
        ]

        self.model.add_subsystem(subsystem_name, ivc, promotes=["*"])
        self.model.set_order([subsystem_name] + previous_order)
