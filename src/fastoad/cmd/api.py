"""
API
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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
import shutil
import sys
from typing import IO, Union

import openmdao.api as om

from fastoad.cmd.exceptions import FastFileExistsError
from fastoad.io.configuration import FASTOADProblem
from fastoad.io.xml import OMXmlIO, OMLegacy1XmlIO
from fastoad.module_management import BundleLoader
from fastoad.module_management.openmdao_system_factory import OpenMDAOSystemFactory
from fastoad.openmdao.connections_utils import build_ivc_of_outputs

# Logger for this module
_LOGGER = logging.getLogger(__name__)

RESOURCE_FOLDER_PATH = pth.join(pth.dirname(__file__), 'resources')
SAMPLE_FILE_PATH = pth.join(RESOURCE_FOLDER_PATH, 'fastoad.toml')


def generate_configuration_file(configuration_file_path: str, overwrite: bool = False):
    """
    Generates a sample configuration file.

    :param configuration_file_path: the path of file to be written
    :param overwrite: if True, the file will be written, even if it already exists
    """
    if not overwrite and pth.exists(configuration_file_path):
        raise FastFileExistsError('Configuration file %s not written because it already exists. '
                                  'Use overwrite=True to bypass.'
                                  % configuration_file_path)

    dirname = pth.dirname(configuration_file_path)
    if not pth.exists(dirname):
        os.makedirs(dirname)
    shutil.copyfile(SAMPLE_FILE_PATH, configuration_file_path)
    _LOGGER.info('Sample configuration written in %s', configuration_file_path)


def generate_inputs(configuration_file_path: str,
                    overwrite: bool = False,
                    source_path: str = None,
                    source_path_schema='native'
                    ):
    """
    Generates input file for the :class:`FASTOADProblem` specified in configuration_file_path.

    :param configuration_file_path: where the path of input file to write is set
    :param overwrite: if True, file will be written even if one already exists
    :param source_path: path of file data will be taken from
    :param source_path_schema: set to 'legacy' if the source file come from legacy FAST
    """
    problem = FASTOADProblem()
    problem.configure(configuration_file_path)

    inputs_path = pth.normpath(problem.input_file_path)
    if not overwrite and pth.exists(inputs_path):
        raise FastFileExistsError('Input file %s not written because it already exists. '
                                  'Use overwrite=True to bypass.'
                                  % inputs_path)

    if source_path:
        if source_path_schema == 'legacy':
            source = OMLegacy1XmlIO(source_path)
        else:
            source = OMXmlIO(source_path)
    else:
        source = None

    problem.write_needed_inputs(source)
    _LOGGER.info('Problem inputs written in %s', inputs_path)


def list_outputs(configuration_file_path: str, out: Union[IO, str] = sys.stdout):
    """
    Writes list of system outputs for the :class:`FASTOADProblem` specified in
    configuration_file_path.

    :param configuration_file_path:
    :param out: the output stream or a path for the output file
    """
    problem = FASTOADProblem()
    problem.configure(configuration_file_path)

    ivc = build_ivc_of_outputs(problem)

    if isinstance(out, str):
        # TODO: manage file overwriting
        out_file = open(out, 'w')
    else:
        out_file = out
    out_file.writelines([
        '-- OUTPUTS OF THE PROBLEM ------------------------------------------------------------\n',
        '%-60s| %s\n' % ('VARIABLE', 'DESCRIPTION')
    ])
    out_file.writelines(['%-60s| %s\n' % (name, attributes['desc']) for (name, _, attributes) in
                         ivc._indep_external])
    out_file.write(
        '--------------------------------------------------------------------------------------\n'
    )

    if isinstance(out, str):
        out_file.close()
        _LOGGER.info('Output list written in %s', out_file)


def list_systems(configuration_file_path: str = None, out: Union[IO, str] = sys.stdout):
    """
    Writes list of available systems.
    If configuration_file_path is given and if it defines paths where there are registered systems,
    they will be listed too.

    :param configuration_file_path:
    :param out: the output stream or a path for the output file
    """

    if configuration_file_path:
        problem = FASTOADProblem()
        problem.configure(configuration_file_path)

    # As the problem has been configured, BundleLoader now knows
    # additional registered systems

    if isinstance(out, str):
        # TODO: manage file overwriting
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
