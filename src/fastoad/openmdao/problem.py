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

from copy import deepcopy

import openmdao.api as om

from fastoad.io import IVariableIOFormatter, VariableIO
from fastoad.openmdao.validity_checker import ValidityDomainChecker
from fastoad.openmdao.variables import VariableList

INPUT_SYSTEM_NAME = "inputs"


class FASTOADProblem(om.Problem):
    """Vanilla OpenMDAO Problem except that it can read and write its variables from/to files.

    It also runs :class:`~fastoad.openmdao.validity_checker.ValidityDomainChecker`
    after each :meth:`run_model` or :meth:`run_driver`
    (but it does nothing if no check has been registered)

    A classical usage of this class would be::

        problem = FASTOADProblem()  # instantiation
        [... configuration as for any OpenMDAO problem ...]

        problem.input_file_path = "inputs.xml"
        problem.output_file_path = "outputs.xml"
        problem.write_needed_inputs()  # writes the input file (defined above) with
                                       # needed variables so user can fill it with proper values
        # or
        problem.write_needed_inputs('previous.xml')  # writes the input file with needed variables
                                                     # and values taken from provided file when
                                                     # available
        problem.read_inputs()    # reads the input file
        problem.run_driver()     # runs the OpenMDAO problem
        problem.write_outputs()  # writes the output file
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_file_path = None
        self.output_file_path = None

    def run_model(self, case_prefix=None, reset_iter_counts=True):
        status = super().run_model(case_prefix, reset_iter_counts)
        ValidityDomainChecker.check_problem_variables(self)
        return status

    def run_driver(self, case_prefix=None, reset_iter_counts=True):
        status = super().run_driver(case_prefix, reset_iter_counts)
        ValidityDomainChecker.check_problem_variables(self)
        return status

    def write_needed_inputs(
        self, source_file_path: str = None, source_formatter: IVariableIOFormatter = None,
    ):
        """
        Writes the input file of the problem with unconnected inputs of the problem.

        Written value of each variable will be taken:
        1. from input_data if it contains the variable
        2. from defined default values in component definitions

        WARNING: if inputs have already been read, they won't be needed any more
        and won't be in written file.

        :param source_file_path: if provided, variable values will be read from it
        :param source_formatter: the class that defines format of input file. if not provided,
                                expected format will be the default one.
        """
        variables = VariableList.from_unconnected_inputs(self, with_optional_inputs=True)
        if source_file_path:
            ref_vars = VariableIO(source_file_path, source_formatter).read()
            variables.update(ref_vars)
            for var in variables:
                var.is_input = True
        writer = VariableIO(self.input_file_path)
        writer.write(variables)

    def read_inputs(self):
        """
        Reads inputs from the configured input file.
        """
        if self.input_file_path:
            # Reads input file
            reader = VariableIO(self.input_file_path)
            variables = reader.read()

            ivc = variables.to_ivc()

            # ivc will be added through add_subsystem, but we must use set_order() to
            # put it first.
            # So we need order of existing subsystem to provide the full order list to
            # set_order() to get order of systems, we use system_iter() that can be used
            # only after setup().
            # But we will not be allowed to use add_subsystem() after setup().
            # So we use setup() on a copy of current instance, and get order from this copy
            tmp_prob = deepcopy(self)
            tmp_prob.setup()
            previous_order = [
                system.name
                for system in tmp_prob.model.system_iter(recurse=False)
                if system.name != "_auto_ivc"
                # OpenMDAO 3.2+ specific : _auto_ivc is an output of system_iter() but is not
                # accepted as input of set_order()
            ]

            self.model.add_subsystem(INPUT_SYSTEM_NAME, ivc, promotes=["*"])
            self.model.set_order([INPUT_SYSTEM_NAME] + previous_order)

    def write_outputs(self):
        """
        Writes all outputs in the configured output file.
        """
        if self.output_file_path:
            writer = VariableIO(self.output_file_path)
            variables = VariableList.from_problem(self)
            writer.write(variables)
