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

from fastoad.io.configuration import ConfiguredProblem
from fastoad.io.xml import OMLegacy1XmlIO, OMXmlIO
from fastoad.module_management import BundleLoader
from fastoad.module_management.openmdao_system_factory import OpenMDAOSystemFactory
from fastoad.openmdao.connections_utils import build_ivc_of_outputs


def query_yes_no(question):
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


class Main:
    """
    Class for managing command line and doing associated actions
    """

    def __init__(self):
        self.parser = ArgumentParser(description='FAST-OAD main program', )
        self.problem = None

    # ACTIONS -----------------------------------------------------------------
    def _generate_inputs(self, args):
        """
        Generates input file according to command line arguments
        """
        if pth.exists(self.problem.input_file_path) and not query_yes_no(
                'Input file "%s" already exists. Do you want to overwrite it?'
                % self.problem.input_file_path):
            print('No file written.')
            return

        if args.source:
            if args.legacy:
                source = OMLegacy1XmlIO(args.source)
            else:
                source = OMXmlIO(args.source)
        else:
            source = None

        self.problem.write_needed_inputs(source)

    def _list_outputs(self, args):
        """
        Prints list of system outputs
        """
        ivc = build_ivc_of_outputs(self.problem)
        print(
            '-- OUTPUTS OF THE PROBLEM ------------------------------------------------------------'
        )
        print('%-60s| %s' % ('VARIABLE', 'DESCRIPTION'))
        for (name, value, attributes) in ivc._indep_external:
            print('%-60s| %s' % (name, attributes['desc']))
        print(
            '--------------------------------------------------------------------------------------'
        )

    @staticmethod
    def _list_systems(args):
        """
        Prints list of system identifiers
        """
        # As the problem has been configured, BundleLoader already knows
        # additional registered systems
        print(
            '-- AVAILABLE SYSTEM IDENTIFIERS ------------------------------------------------------'
        )
        print('%-60s| %s' % ('IDENTIFIER', 'PATH'))
        for identifier in OpenMDAOSystemFactory.get_system_ids():
            path = BundleLoader().get_factory_path(identifier)
            print('%-60s| %s' % (identifier, path))
        print(
            '--------------------------------------------------------------------------------------'
        )

    def _evaluate(self, args):
        """
        Runs model according to provided problem file
        """
        if pth.exists(self.problem.output_file_path) and not query_yes_no(
                'Output file "%s" already exists. Do you want to overwrite it?'
                % self.problem.output_file_path):
            print('Computation interrupted.')
            return

        self.problem.read_inputs()
        self.problem.run_model()
        self.problem.write_outputs()

    def _optimize(self, args):
        """
        Runs driver according to provided problem file
        """
        if pth.exists(self.problem.output_file_path) and not query_yes_no(
                'Output file "%s" already exists. Do you want to overwrite it?'
                % self.problem.output_file_path):
            print('Computation interrupted.')
            return

        self.problem.read_inputs()
        self.problem.run_driver()
        self.problem.write_outputs()

    # PARSER CONFIGURATION ----------------------------------------------------
    def _add_conf_file_argument(self, parser: ArgumentParser, required=True):
        kwargs = {
            'type': str,
            'help': 'the configuration file for setting the problem'
        }
        if not required:
            kwargs['nargs'] = '?'
        parser.add_argument('conf_file', **kwargs)
        parser.set_defaults(set_problem=self._set_problem)

    def _set_problem(self, args):
        """
        Initialize the OpenMDAO problem id conf_file has been provided
        """
        if args.conf_file:
            self.problem = ConfiguredProblem()
            self.problem.configure(args.conf_file)

    # ENTRY POINT -------------------------------------------------------------
    def run(self):
        """ Main function """
        # self.parser.add_argument('conf_file', type=str, nargs='?',
        #                          help='the configuration file for setting the problem')
        # self.parser.set_defaults(func=self._set_problem)

        subparsers = self.parser.add_subparsers(title='sub-commands')

        # sub-command for generating input file -----------
        parser_gen_inputs = subparsers.add_parser(
            'gen_inputs',
            formatter_class=RawDescriptionHelpFormatter,
            description=
            'generates the input file (specified in the configuration file) with needed variables')
        self._add_conf_file_argument(parser_gen_inputs)
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
        parser_run_model.set_defaults(func=self._evaluate)

        # sub-command for running the driver --------------
        parser_run_driver = subparsers.add_parser(
            'optim',
            description='Runs the optimization')
        self._add_conf_file_argument(parser_run_driver)
        parser_run_driver.set_defaults(func=self._optimize)

        args = self.parser.parse_args()
        args.set_problem(args)
        args.func(args)


def main():
    Main().run()


if __name__ == '__main__':
    main()
