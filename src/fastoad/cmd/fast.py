"""
main
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

import os.path as pth
from argparse import ArgumentParser
from distutils.util import strtobool

from fastoad.io.configuration import ConfiguredProblem
from fastoad.io.xml import OMLegacy1XmlIO, OMXmlIO
from fastoad.module_management import BundleLoader
from fastoad.module_management.openmdao_system_factory import OpenMDAOSystemFactory


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


def gen_inputs(args):
    """
    Generates input file according to command line arguments
    """
    problem = ConfiguredProblem()
    problem.configure(args.conf_file)

    if pth.exists(problem.input_file_path) and not _query_yes_no(
            'Input file "%s" already exists. Do you want to overwrite it?'
            % problem.input_file_path):
        print('No file written.')
        return

    if args.source:
        if args.legacy:
            source = OMLegacy1XmlIO(args.source)
        else:
            source = OMXmlIO(args.source)
    else:
        source = None

    problem.write_needed_inputs(source)


def list_systems(args):
    """
    Prints list of system identifiers
    """
    if args.conf_file:
        problem = ConfiguredProblem()
        problem.configure(args.conf_file)

    print('-- AVAILABLE SYSTEM IDENTIFIERS -------------------------------------------------------')
    print('%-60s %s' % ('IDENTIFIER', 'PATH'))
    for identifier in OpenMDAOSystemFactory.get_system_ids():
        path = BundleLoader().get_factory_path(identifier)
        print('%-60s %s' % (identifier, path))
    print('---------------------------------------------------------------------------------------')


def run_model(args):
    """
    Runs model according to provided problem file
    """
    problem = ConfiguredProblem()
    problem.configure(args.conf_file)

    if pth.exists(problem.output_file_path) and _query_yes_no(
            'Output file "%s" already exists. Do you want to overwrite it?'
            % problem.output_file_path):
        print('Computation interrupted.')
        return

    problem.read_inputs()
    problem.run_model()
    problem.write_outputs()


def run_driver(args):
    """
    Runs driver according to provided problem file
    """
    problem = ConfiguredProblem()
    problem.configure(args.conf_file)

    if pth.exists(problem.output_file_path) and _query_yes_no(
            'Output file "%s" already exists. Do you want to overwrite it?'
            % problem.output_file_path):
        print('Computation interrupted.')
        return

    problem.read_inputs()
    problem.run_driver()
    problem.write_outputs()


def main():
    """ Main function """
    parser = ArgumentParser(description='FAST-OAD main program')
    parser.add_argument('conf_file', type=str, nargs='?',
                        help='the configuration file for setting the problem')

    subparsers = parser.add_subparsers(title='sub-commands')

    parser_gen_inputs = subparsers.add_parser(
        'gen_inputs',
        help='generates the input file (specified in the configuration file) with needed variables')
    parser_gen_inputs.add_argument(
        'source', nargs='?',
        help='if provided, generated input file will be fed with values from provided XML file')
    parser_gen_inputs.add_argument(
        '--legacy',
        help='to be used if the source XML file is in legacy format')
    parser_gen_inputs.set_defaults(func=gen_inputs)

    parser_run_model = subparsers.add_parser(
        'run_model',
        help='runs the analysis')
    parser_run_model.set_defaults(func=run_model)

    parser_run_driver = subparsers.add_parser(
        'run_driver',
        help='runs the optimization')
    parser_run_driver.set_defaults(func=run_driver)

    parser_list_systems = subparsers.add_parser(
        'list_systems',
        help='provides the identifiers of available systems')
    parser_list_systems.set_defaults(func=list_systems)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
