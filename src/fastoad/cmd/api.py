"""
API
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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
import os
import os.path as pth
import sys
from typing import IO, Union

import openmdao.api as om
from importlib_resources import read_binary

from fastoad.cmd.exceptions import FastFileExistsError
from fastoad.io.configuration import FASTOADProblem
from fastoad.io.xml import OMXmlIO, OMLegacy1XmlIO
from fastoad.module_management import BundleLoader
from fastoad.module_management.openmdao_system_factory import OpenMDAOSystemFactory
from fastoad.openmdao.connections_utils import get_unconnected_input_variables, \
    get_variables_from_problem
from . import resources

# Logger for this module
_LOGGER = logging.getLogger(__name__)

SAMPLE_FILENAME = 'fastoad.toml'


def generate_configuration_file(configuration_file_path: str, overwrite: bool = False):
    """
    Generates a sample configuration file.

    :param configuration_file_path: the path of file to be written
    :param overwrite: if True, the file will be written, even if it already exists
    :raise FastFileExistsError: if overwrite==False and configuration_file_path already exists
    """
    if not overwrite and pth.exists(configuration_file_path):
        raise FastFileExistsError('Configuration file %s not written because it already exists. '
                                  'Use overwrite=True to bypass.'
                                  % configuration_file_path)

    dirname = pth.abspath(pth.dirname(configuration_file_path))
    if not pth.exists(dirname):
        os.makedirs(dirname)

    with open(configuration_file_path, 'wb') as conf_file:
        conf_file.write(read_binary(resources, SAMPLE_FILENAME))
    _LOGGER.info('Sample configuration written in %s', configuration_file_path)


def generate_inputs(configuration_file_path: str,
                    source_path: str = None,
                    source_path_schema='native',
                    overwrite: bool = False
                    ):
    """
    Generates input file for the :class:`FASTOADProblem` specified in configuration_file_path.

    :param configuration_file_path: where the path of input file to write is set
    :param source_path: path of file data will be taken from
    :param source_path_schema: set to 'legacy' if the source file come from legacy FAST
    :param overwrite: if True, file will be written even if one already exists
    :raise FastFileExistsError: if overwrite==False and configuration_file_path already exists
    """
    problem = FASTOADProblem()
    problem.configure(configuration_file_path)

    inputs_path = pth.normpath(problem.input_file_path)
    if not overwrite and pth.exists(inputs_path):
        raise FastFileExistsError('Input file %s not written because it already exists. '
                                  'Use overwrite=True to bypass.'
                                  % inputs_path, inputs_path)

    if source_path:
        if source_path_schema == 'legacy':
            source = OMLegacy1XmlIO(source_path)
        else:
            source = OMXmlIO(source_path)
    else:
        source = None

    problem.write_needed_inputs(source)
    _LOGGER.info('Problem inputs written in %s', inputs_path)


def list_variables(configuration_file_path: str,
                   out: Union[IO, str] = sys.stdout,
                   overwrite: bool = False):
    """
    Writes list of system outputs for the :class:`FASTOADProblem` specified in
    configuration_file_path.

    :param configuration_file_path:
    :param out: the output stream or a path for the output file
    :param overwrite: if True and out is a file path, the file will be written even if one already
                      exists
    :raise FastFileExistsError: if overwrite==False and out is a file path and the file exists
    """
    problem = FASTOADProblem()
    problem.configure(configuration_file_path)

    input_variables = get_unconnected_input_variables(problem, with_optional_inputs=True)
    output_variables = get_variables_from_problem(problem, use_inputs=False)

    if isinstance(out, str):
        if not overwrite and pth.exists(out):
            raise FastFileExistsError('File %s not written because it already exists. '
                                      'Use overwrite=True to bypass.'
                                      % out)
        out_file = open(out, 'w')
    else:
        out_file = out

    # Inputs
    out_file.writelines([
        '-- INPUTS OF THE PROBLEM -------------------------------------------------------------\n',
        '%-60s| %s\n' % ('VARIABLE', 'DESCRIPTION')
    ])
    out_file.writelines(['%-60s| %s\n' % (var.name, var.description) for var in input_variables])
    out_file.write(
        '--------------------------------------------------------------------------------------\n'
    )

    # Outputs
    out_file.writelines([
        '-- OUTPUTS OF THE PROBLEM ------------------------------------------------------------\n',
        '%-60s| %s\n' % ('VARIABLE', 'DESCRIPTION')
    ])
    out_file.writelines(['%-60s| %s\n' % (var.name, var.description) for var in output_variables])
    out_file.write(
        '--------------------------------------------------------------------------------------\n'
    )

    if isinstance(out, str):
        out_file.close()
        _LOGGER.info('Output list written in %s', out_file)


def list_systems(configuration_file_path: str = None,
                 out: Union[IO, str] = sys.stdout,
                 overwrite: bool = False):
    """
    Writes list of available systems.
    If configuration_file_path is given and if it defines paths where there are registered systems,
    they will be listed too.

    :param configuration_file_path:
    :param out: the output stream or a path for the output file
    :param overwrite: if True and out is a file path, the file will be written even if one already
                      exists
    :raise FastFileExistsError: if overwrite==False and out is a file path and the file exists
    """

    if configuration_file_path:
        problem = FASTOADProblem()
        problem.configure(configuration_file_path)
    # As the problem has been configured, BundleLoader now knows additional registered systems

    if isinstance(out, str):
        if not overwrite and pth.exists(out):
            raise FastFileExistsError('File %s not written because it already exists. '
                                      'Use overwrite=True to bypass.'
                                      % out)
        out_file = open(out, 'w')
    else:
        out_file = out
    out_file.writelines([
        '-- AVAILABLE SYSTEM IDENTIFIERS ------------------------------------------------------\n',
        '%-60s| %s\n' % ('IDENTIFIER', 'PATH')
    ])
    for identifier in OpenMDAOSystemFactory.get_system_ids():
        path = BundleLoader().get_factory_path(identifier)
        out_file.write('%-60s| %s\n' % (identifier, path))
    out_file.write(
        '--------------------------------------------------------------------------------------\n'
    )

    if isinstance(out, str):
        out_file.close()
        _LOGGER.info('System list written in %s', out_file)


def write_n2(configuration_file_path: str, n2_file_path: str = None, overwrite: bool = False):
    """
    Write the N2 diagram of the problem in file n2.html

    :param configuration_file_path:
    :param n2_file_path:
    :param overwrite:
    """

    if not n2_file_path:
        n2_file_path = pth.join(pth.dirname(configuration_file_path), 'n2.html')
    n2_file_path = pth.normpath(n2_file_path)

    if not overwrite and pth.exists(n2_file_path):
        raise FastFileExistsError('N2-diagram file %s not written because it already exists. '
                                  'Use overwrite=True to bypass.'
                                  % n2_file_path)

    problem = FASTOADProblem()
    problem.configure(configuration_file_path)

    om.n2(problem, outfile=n2_file_path, show_browser=False)
    _LOGGER.info('N2 diagram written in %s', n2_file_path)


def _run_problem(configuration_file_path: str,
                 overwrite: bool = False,
                 mode='run_model') -> FASTOADProblem:
    """
    Runs problem according to provided file

    :param configuration_file_path: problem definition
    :param overwrite: if True, output file will be overwritten
    :param mode: 'run_model' or 'run_driver'
    :return: the OpenMDAO problem after run
    """

    problem = FASTOADProblem()
    problem.configure(configuration_file_path)

    outputs_path = pth.normpath(problem.output_file_path)
    if not overwrite and pth.exists(outputs_path):
        raise FastFileExistsError('Problem not run because output file %s already exists. '
                                  'Use overwrite=True to bypass.'
                                  % outputs_path)

    problem.read_inputs()
    problem.setup()
    if mode == 'run_model':
        problem.run_model()
    else:
        problem.run_driver()
    problem.write_outputs()
    _LOGGER.info('Computation finished. Problem outputs written in %s', outputs_path)

    return problem


def evaluate_problem(configuration_file_path: str, overwrite: bool = False) -> FASTOADProblem:
    """
    Runs model according to provided problem file

    :param configuration_file_path: problem definition
    :param overwrite: if True, output file will be overwritten
    :return: the OpenMDAO problem after run
    """
    return _run_problem(configuration_file_path, overwrite, 'run_model')


def optimize_problem(configuration_file_path: str, overwrite: bool = False) -> FASTOADProblem:
    """
    Runs driver according to provided problem file

    :param configuration_file_path: problem definition
    :param overwrite: if True, output file will be overwritten
    :return: the OpenMDAO problem after run
    """
    return _run_problem(configuration_file_path, overwrite, 'run_driver')
