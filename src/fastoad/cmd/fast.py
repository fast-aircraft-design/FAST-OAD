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
import textwrap
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from distutils.util import strtobool

from fastoad.cmd import api
from fastoad.cmd.exceptions import FastFileExistsError

RESOURCE_FOLDER_PATH = pth.join(pth.dirname(__file__), 'resources')


# TODO: it has become a bit messy down here... Refactoring needed, maybe
#       with a better organization of code by sub-commands


class Main:
    """
    Class for managing command line and doing associated actions
    """

    def __init__(self):
        self.parser = ArgumentParser(description='FAST-OAD main program', )
        self.problem = None

    # ACTIONS -----------------------------------------------------------------
    @staticmethod
    def _generate_conf_file(args):
        """
        Generates a sample TOML file
        """
        try:
            api.generate_configuration_file(args.conf_file, args.force)
        except FastFileExistsError:
            if _query_yes_no(
                    'Configuration file "%s" already exists. Do you want to overwrite it?'
                    % args.conf_file):
                api.generate_configuration_file(args.conf_file, True)
            else:
                print('No file written.')

    @staticmethod
    def _generate_inputs(args):
        """
        Generates input file according to command line arguments
        """
        schema = 'legacy' if args.legacy else 'native'
        try:
            api.generate_inputs(args.conf_file, args.force, args.source, schema)
        except FastFileExistsError:
            if _query_yes_no(
                    'Input file "%s" already exists. Do you want to overwrite it?'
                    % args.conf_file):
                api.generate_inputs(args.conf_file, True, args.source, schema)
            else:
                print('No file written.')

    @staticmethod
    def _list_outputs(args):
        """
        Prints list of system outputs
        """
        api.list_outputs(args.conf_file)

    @staticmethod
    def _list_systems(args):
        """
        Prints list of system identifiers
        """
        api.list_systems(args.conf_file)

    @staticmethod
    def _evaluate(args):
        """
        Runs model according to provided problem file
        """
        try:
            api.evaluate_problem(args.conf_file, args.force)
        except FastFileExistsError:
            if _query_yes_no(
                    'Output file "%s" already exists. Do you want to overwrite it?'
                    % args.conf_file):
                api.evaluate_problem(args.conf_file, True)
            else:
                print('Computation not run.')

    @staticmethod
    def _optimize(args):
        """
        Runs driver according to provided problem file
        """
        try:
            api.optimize_problem(args.conf_file, args.force)
        except FastFileExistsError:
            if _query_yes_no(
                    'Output file "%s" already exists. Do you want to overwrite it?'
                    % args.conf_file):
                api.optimize_problem(args.conf_file, True)
            else:
                print('Computation not run.')

    # PARSER CONFIGURATION ----------------------------------------------------
    @staticmethod
    def _add_conf_file_argument(parser: ArgumentParser, required=True):
        kwargs = {
            'type': str,
            'help': 'the configuration file for setting the problem'
        }
        if not required:
            kwargs['nargs'] = '?'
        parser.add_argument('conf_file', **kwargs)

    @staticmethod
    def _add_overwrite_argument(parser: ArgumentParser):
        parser.add_argument('-f', '--force', action='store_true',
                            help='do not ask before overwriting files')

    # ENTRY POINT -------------------------------------------------------------
    def run(self):
        """ Main function """

        subparsers = self.parser.add_subparsers(title='sub-commands')

        # sub-command for generating sample configuration file -----------
        parser_gen_conf = subparsers.add_parser(
            'gen_conf',
            formatter_class=RawDescriptionHelpFormatter,
            description=
            'generates the configuration file with sample data')
        parser_gen_conf.add_argument('conf_file', type=str, help='the name of configuration file '
                                                                 'to be written')
        self._add_overwrite_argument(parser_gen_conf)
        parser_gen_conf.set_defaults(func=self._generate_conf_file)

        # sub-command for generating input file -----------
        parser_gen_inputs = subparsers.add_parser(
            'gen_inputs',
            formatter_class=RawDescriptionHelpFormatter,
            description=
            'generates the input file (specified in the configuration file) with needed variables')
        self._add_conf_file_argument(parser_gen_inputs)
        self._add_overwrite_argument(parser_gen_inputs)
        parser_gen_inputs.add_argument(
            'source', nargs='?',
            help='if provided, generated input file will be fed with values from provided XML file')
        parser_gen_inputs.add_argument(
            '--legacy',
            help='to be used if the source XML file is in legacy format')
        parser_gen_inputs.set_defaults(func=self._generate_inputs)
        parser_gen_inputs.epilog = textwrap.dedent('''\
            Examples:
            ---------
            # For the problem defined in conf_file.toml, generates the input file with default 
            # values (when default values are defined):
                %(prog)s gen_inputs conf_file.toml
            
            # Same as above, except that values are taken from some_file.xml when possible:
                %(prog)s gen_inputs conf_file.toml some_file.xml

            # Same as above, some_file.xml is in the legacy FAST schema
                %(prog)s gen_inputs conf_file.toml some_file.xml --legacy
            ''')

        # sub-command for listing registered systems ------
        parser_list_systems = subparsers.add_parser(
            'list_systems',
            description='Provides the identifiers of available systems')
        self._add_conf_file_argument(parser_list_systems, required=False)
        parser_list_systems.set_defaults(func=self._list_systems)

        # sub-command for listing possible outputs --------
        parser_list_outputs = subparsers.add_parser(
            'list_outputs',
            description='Provides the outputs of the problem')
        self._add_conf_file_argument(parser_list_outputs)
        parser_list_outputs.set_defaults(func=self._list_outputs)

        # sub-command for running the model ---------------
        parser_run_model = subparsers.add_parser(
            'eval',
            description='Runs the analysis')
        self._add_conf_file_argument(parser_run_model)
        self._add_overwrite_argument(parser_run_model)
        parser_run_model.set_defaults(func=self._evaluate)

        # sub-command for running the driver --------------
        parser_run_driver = subparsers.add_parser(
            'optim',
            description='Runs the optimization')
        self._add_conf_file_argument(parser_run_driver)
        self._add_overwrite_argument(parser_run_driver)
        parser_run_driver.set_defaults(func=self._optimize)

        args = self.parser.parse_args()
        args.func(args)


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


def main():
    Main().run()


if __name__ == '__main__':
    main()
