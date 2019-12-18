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

import os
import os.path as pth
import shutil
import sys
from distutils.util import strtobool
from typing import IO

from fastoad.io.configuration import ConfiguredProblem
from fastoad.io.xml import OMXmlIO, OMLegacy1XmlIO
from fastoad.module_management import BundleLoader
from fastoad.module_management.openmdao_system_factory import OpenMDAOSystemFactory
from fastoad.openmdao.connections_utils import build_ivc_of_outputs

RESOURCE_FOLDER_PATH = pth.join(pth.dirname(__file__), 'resources')


def generate_configuration_file(configuration_file_path: str, overwrite: bool = False):
    """
    Generates a sample configuration file.

    :param configuration_file_path: the path of file to be written
    :param overwrite: if True, the file will be written, even if it already exists
    """
    sample_file_path = pth.join(RESOURCE_FOLDER_PATH, 'fastoad.toml')
    if not _can_write(configuration_file_path, overwrite):
        return

    dirname = pth.dirname(configuration_file_path)
    if not pth.exists(dirname):
        os.makedirs(dirname)
    shutil.copyfile(sample_file_path, configuration_file_path)
    print('Sample configuration written in %s' % configuration_file_path)


def generate_inputs(configuration_file_path: str,
                    overwrite: bool = False,
                    source_path: str = None,
                    source_path_schema='native'
                    ):
    """
    Generates input file for the specified :class:`ConfiguredProblem`

    :param configuration_file_path: where the path of input file to write is set
    :param overwrite: if True, file will be written even if one already exists
    :param source_path: path of file data will be taken from
    :param source_path_schema: set to 'legacy' if the source file come from legacy FAST
    """
    problem = ConfiguredProblem()
    problem.configure(configuration_file_path)

    inputs_path = pth.normpath(problem.input_file_path)
    if not _can_write(inputs_path, overwrite):
        return

    if source_path:
        if source_path_schema == 'legacy':
            source = OMLegacy1XmlIO(source_path)
        else:
            source = OMXmlIO(source_path)
    else:
        source = None

    problem.write_needed_inputs(source)
    print('Problem inputs written in %s' % inputs_path)


def list_outputs(configuration_file_path: str, out: IO = sys.stdout):
    """
    Prints list of system outputs
    """
    problem = ConfiguredProblem()
    problem.configure(configuration_file_path)

    ivc = build_ivc_of_outputs(problem)

    if isinstance(out, str):
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


def list_systems(configuration_file_path: str = None, out: IO = sys.stdout):
    """
    Prints list of system identifiers
    """

    if configuration_file_path:
        problem = ConfiguredProblem()
        problem.configure(configuration_file_path)

    # As the problem has been configured, BundleLoader now knows
    # additional registered systems

    if isinstance(out, str):
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


def _run_problem(configuration_file_path: str, overwrite: bool = False, mode='run_model'):
    """
    Runs problem according to provided file

    :param configuration_file_path: problem definition
    :param overwrite: if True, output file will be overwritten
    :param mode: 'run_model' or 'run_driver'
    :return: the OpenMDAO problem
    """

    problem = ConfiguredProblem()
    problem.configure(configuration_file_path)

    outputs_path = pth.normpath(problem.output_file_path)
    if not _can_write(outputs_path, overwrite):
        return

    if not overwrite and pth.exists(outputs_path) and not _query_yes_no(
            'Output file "%s" already exists. Do you want to overwrite it?'
            % outputs_path):
        print('Computation interrupted.')
        return

    problem.read_inputs()
    problem.setup()
    if mode == 'run_model':
        problem.run_model()
    else:
        problem.run_driver()
    problem.write_outputs()
    print('Computation finished. Problem outputs written in %s' % outputs_path)

    return problem


def evaluate_problem(configuration_file_path: str, overwrite: bool = False):
    """
    Runs model according to provided problem file

    :param configuration_file_path: problem definition
    :param overwrite: if True, output file will be overwritten
    :return: the OpenMDAO problem
    """
    return _run_problem(configuration_file_path, overwrite, 'evaluate')


def optimize_problem(configuration_file_path: str, overwrite: bool = False):
    """
    Runs driver according to provided problem file

    :param configuration_file_path: problem definition
    :param overwrite: if True, output file will be overwritten
    :return: the OpenMDAO problem
    """
    return _run_problem(configuration_file_path, overwrite, 'optimize')


# TODO: Must this class fusioned with ConfiguredProblem?
class FastProblem(ConfiguredProblem):

    def __init__(self, conf_file, *args, **kwargs):
        import warnings
        warnings.warn('Use functions from api.py instead', DeprecationWarning)
        super().__init__(*args, **kwargs)
        self.configure(conf_file)

    def gen_inputs(self):
        self.write_needed_inputs()

    def gen_inputs_from(self, input_file=None):
        self.write_needed_inputs(OMXmlIO(input_file))

    def gen_inputs_from_legacy(self, input_file=None):
        self.write_needed_inputs(OMLegacy1XmlIO(input_file))

    def run_eval(self):
        self.read_inputs()
        self.run_model()
        self.write_outputs()

    def run_optim(self):
        self.read_inputs()
        self.run_driver()
        self.write_outputs()


def _query_yes_no(question):
    """
    Ask a yes/no question via input() and return its answer as boolean.

    Keeps asking while answer is not similar to "yes" or "no"
    The returned value is True for "yes" or False for "no".
    """
    answer = None
    while answer is None:
        raw_answer = input(question + '\n')
        try:
            answer = strtobool(raw_answer)
        except ValueError:
            pass

    return answer == 1


def _is_interactive():
    """
    :return: True if Python in interactive mode
    """
    return hasattr(sys, 'ps1')


def _can_write(file_path: str, overwrite: bool) -> bool:
    """
    Checks if file exists and if it can be overwritten.
    If file exists and overwrite is set to False:
     - in Python interactive mode, simply prints an informative message and returns without writing the file
     - in console mode, asks for confirmation

    :param file_path:
    :param overwrite:
    :return: True if file can be written
    """

    if not overwrite and pth.exists(file_path):
        if _is_interactive():
            print('File exists. To write it anyway, please call again with overwrite set to True')
            return False
        elif not _query_yes_no(
                'File "%s" already exists. Do you want to overwrite it?'
                % file_path):
            print('No file written.')
            return False
    return True
