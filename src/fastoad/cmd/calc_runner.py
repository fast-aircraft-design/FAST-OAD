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
from pathlib import Path
from typing import List, Optional, Union

from openmdao.utils.mpi import FakeComm

from fastoad._utils.files import as_path, make_parent_dir
from fastoad.io import DataFile
from fastoad.io.configuration import FASTOADProblemConfigurator
from fastoad.openmdao.variables import VariableList

# Import MPI4Py at the module level to avoid repeated imports
try:
    from mpi4py import MPI
    from mpi4py.futures import MPIPoolExecutor
except ImportError:
    HAVE_MPI = False
else:
    HAVE_MPI = True

_LOGGER = logging.getLogger(__name__)  # Logger for this module


@dataclass
class CalcRunner:
    """
    Class for running FAST-OAD computations for a specific configuration.

    It is specifically designed to run several computations concurrently with
    :meth:`run_cases`.
    For each computation, data can be isolated in a specific folder.
    """

    #: Configuration file, common to all computations
    configuration_file_path: Union[str, PathLike]

    #: Input file for the computation (will supersede the input file setting in
    #  configuration file)
    input_file_path: Optional[Union[str, PathLike]] = None

    #: For activating MDO instead MDA
    optimize: bool = False

    def __post_init__(self):
        # Let's ensure we have absolute paths
        self.configuration_file_path = as_path(self.configuration_file_path).resolve()
        if self.input_file_path:
            self.input_file_path = as_path(self.input_file_path).resolve()

    def run(
        self,
        input_values: Optional[VariableList] = None,
        calculation_folder: Optional[Union[str, PathLike]] = None,
    ) -> DataFile:
        """
        Run the computation.

        This method is useful to set input values on-the-fly, and/or isolate the
        computation data in a dedicated folder.

        :param input_values: if provided, these values will supersede the content
                             of input file (specified in configuration file)
        :param calculation_folder: if specified, all data, including configuration file,
                                   will be stored in that folder. The input file in this folder
                                   will contain data from `input_values`

        :return: the written output data
        """
        configuration = FASTOADProblemConfigurator(self.configuration_file_path)

        if self.input_file_path:
            configuration.input_file_path = self.input_file_path

        if calculation_folder:
            make_parent_dir(calculation_folder)
            configuration.make_local(calculation_folder)
            if input_values:
                input_data = DataFile(configuration.input_file_path)
                input_data.update(input_values)
                input_data.save()

        problem = configuration.get_problem(read_inputs=True)
        problem.comm = FakeComm()
        problem.setup()

        if input_values and not calculation_folder:
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
        *,
        max_workers: Optional[int] = None,
        use_MPI_if_available: bool = True,
        overwrite_subfolders: bool = False,
    ):
        """
        Run computations concurrently.

        The data of each computation will be isolated in a dedicated subfolder of
        `destination folder`.

        :param input_list: a computation will be run for each item of this list
        :param destination_folder:  The data of each computation will be isolated in a dedicated
                                    subfolder of this folder.
        :param max_workers: if not specified, all available processors will be used. Set to -1
                            to use all available processors except 1 (useful when running
                            locally while keeping some CPU for working meanwhile).
        :param use_MPI_if_available: If False, or if no MPI implementation is available,
                                     computations will be run concurrently using the multiprocessing
                                     library.
        :param overwrite_subfolders: if False, calculations that match existing subfolders won't be
                                     run (allows batch continuation)
        """
        destination_folder = as_path(destination_folder).resolve()

        use_MPI = use_MPI_if_available and HAVE_MPI
        if use_MPI_if_available and not HAVE_MPI:
            _LOGGER.warning("No MPI environment found. Using multiprocessing instead.")

        # One worker is consumed by the MPIPoolExecutor
        max_proc = (MPI.COMM_WORLD.Get_size() - 1) if use_MPI else mp.cpu_count()

        if max_workers == -1:
            max_workers = max_proc - 1
        elif max_workers is not None:
            max_workers = max(1, min(max_workers, max_proc))

        pool_cls = _MPIPool if use_MPI else mp.Pool

        with pool_cls(max_workers) as pool:
            pool.starmap(
                CalcRunner.run,
                self._calculation_inputs(input_list, destination_folder, overwrite_subfolders),
                # If a computation crashes, the whole chunk stops.
                # chunksize=1 ensures all computations will be launched.
                chunksize=1,
            )

    def _calculation_inputs(
        self,
        input_list: List[VariableList],
        destination_folder: Path,
        overwrite_subfolders: bool,
    ):
        """Iterator for providing inputs of :meth:`run`."""
        case_count = len(input_list)
        n_digits = ceil(log10(case_count))

        for i, input_vars in enumerate(input_list):
            calculation_folder = destination_folder / f"calc_{i:0{n_digits}d}"
            if overwrite_subfolders or not calculation_folder.is_dir():
                yield self, input_vars, calculation_folder
            else:
                _LOGGER.info('Subfolder "%s" exists. Computation skipped', calculation_folder)


@contextmanager
def _MPIPool(*args, **kwargs):
    """Assumes availability of MPI environment."""

    pool = MPIPoolExecutor(*args, main=False, **kwargs)
    try:
        yield pool
    finally:
        pool.shutdown()
