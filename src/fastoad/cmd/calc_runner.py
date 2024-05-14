"""Tools for running multiple computations"""
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
import multiprocessing as mp
from contextlib import contextmanager
from dataclasses import dataclass
from math import ceil, log10
from os import PathLike
from typing import List, Optional, Union

from openmdao.utils.mpi import FakeComm

from fastoad._utils.files import as_path, make_parent_dir
from fastoad.io.configuration import FASTOADProblemConfigurator
from fastoad.openmdao.variables import VariableList

_LOGGER = logging.getLogger(__name__)  # Logger for this module


@dataclass
class RunCase:
    configuration_file_path: Optional[Union[str, PathLike]]
    optimize: bool = False

    def run(
        self,
        input_values: Optional[VariableList] = None,
        calculation_folder: Optional[Union[str, PathLike]] = None,
    ):
        """
        Run the computation.

        :param input_values:
        :param calculation_folder:
        :return:
        """
        configuration = FASTOADProblemConfigurator(self.configuration_file_path)
        if calculation_folder:
            make_parent_dir(calculation_folder)
            configuration.make_local(calculation_folder)

        problem = configuration.get_problem(read_inputs=True)
        problem.comm = FakeComm()
        problem.setup()

        if input_values:
            for input_variable in input_values:
                problem.set_val(
                    input_variable.name,
                    val=input_variable.val,
                    units=input_variable.units,
                )

        if self.optimize:
            problem.run_driver()
        else:
            problem.run_model()

        output_data = problem.write_outputs()

        return output_data

    def run_cases(
        self,
        input_list: List[VariableList],
        destination_folder: Union[str, PathLike],
        n_proc: Optional[int] = None,
        use_MPI_if_available: bool = True,
    ):
        """

        :param input_list:
        :param destination_folder:
        :param n_proc:
        :param use_MPI_if_available:
        :return:
        """
        destination_folder = as_path(destination_folder)
        if n_proc == 0:
            n_proc = mp.cpu_count() - 1

        case_count = len(input_list)
        n_digits = ceil(log10(case_count))

        calculation_inputs = []
        for i, input_vars in enumerate(input_list):
            calculation_folder = destination_folder / f"calc_{i:0{n_digits}d}"
            calculation_inputs.append((self, input_vars, calculation_folder))

        use_MPI = False
        max_proc = mp.cpu_count()
        if use_MPI_if_available:
            try:
                from mpi4py import MPI  # noqa: F401

                use_MPI = True
                max_proc = MPI.COMM_WORLD.Get_size()
            except ImportError:
                _LOGGER.warning("No MPI environment found. Using multiprocessing instead.")
                pass

        if n_proc is not None:
            n_proc = min(n_proc, max_proc)

        if use_MPI:
            pool = _MPIPool
        else:
            pool = mp.Pool

        with pool(n_proc) as pool:
            pool.starmap(RunCase.run, calculation_inputs)


@contextmanager
def _MPIPool(*args, **kwargs):
    """Assumes availability of MPI environment."""
    from mpi4py.futures import MPIPoolExecutor

    pool = MPIPoolExecutor(*args, **kwargs)
    try:
        yield pool
    finally:
        pool.shutdown()
