"""Command Line Interface."""
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

import logging
import os
import os.path as pth
import shutil
import textwrap
from argparse import ArgumentParser, RawDescriptionHelpFormatter, ArgumentDefaultsHelpFormatter
from distutils.util import strtobool

import fastoad
from fastoad.cmd import api
from fastoad.cmd.exceptions import FastFileExistsError
from fastoad.utils.resource_management.copy import copy_resource_folder

NOTEBOOK_FOLDER_NAME = "FAST_OAD_notebooks"


# TODO: it has become a bit messy down here... Refactoring needed, maybe
#       with a better organization of code by sub-commands


class Main:
    """
    Class for managing command line and doing associated actions
    """

    def __init__(self):
        class _CustomFormatter(RawDescriptionHelpFormatter, ArgumentDefaultsHelpFormatter):
            pass

        self.parser = ArgumentParser(
            description="FAST-OAD main program", formatter_class=_CustomFormatter
        )
        self.problem = None

    # ACTIONS ======================================================================================
    @staticmethod
    def _generate_conf_file(args):
        """Generates a sample TOML file."""
        try:
            api.generate_configuration_file(args.conf_file, args.force)
        except FastFileExistsError:
            if _query_yes_no(
                'Configuration file "%s" already exists. Do you want to overwrite it?'
                % args.conf_file
            ):
                api.generate_configuration_file(args.conf_file, True)
            else:
                print("No file written.")

    @staticmethod
    def _generate_inputs(args):
        """Generates input file according to command line arguments."""
        schema = "legacy" if args.legacy else "native"
        try:
            api.generate_inputs(args.conf_file, args.source, schema, args.force)
        except FastFileExistsError as exc:
            if _query_yes_no(
                'Input file "%s" already exists. Do you want to overwrite it?' % exc.args[1]
            ):
                api.generate_inputs(args.conf_file, args.source, schema, True)
            else:
                print("No file written.")

    @staticmethod
    def _list_systems(args):
        """Prints list of system identifiers."""
        api.list_systems(args.conf_file)

    @staticmethod
    def _list_variables(args):
        """Prints list of system outputs."""
        api.list_variables(args.conf_file)

    @staticmethod
    def _write_n2(args):
        """Creates N2 html file."""
        try:
            api.write_n2(args.conf_file, args.n2_file, args.force)
        except FastFileExistsError:
            if _query_yes_no(
                'N2 file "%s" already exists. Do you want to overwrite it?' % args.n2_file
            ):
                api.write_n2(args.conf_file, args.n2_file, True)
            else:
                print("No file written.")

    @staticmethod
    def _write_xdsm(args):
        """Creates XDSM html file."""

        def _write(overwrite):
            api.write_xdsm(
                args.conf_file,
                args.xdsm_file,
                overwrite=overwrite,
                wop_server_url=args.wop_server,
                depth=args.depth,
            )

        try:
            _write(args.force)
        except FastFileExistsError:
            if _query_yes_no(
                'XDSM file "%s" already exists. Do you want to overwrite it?' % args.xdsm_file
            ):
                _write(True)
            else:
                print("No file written.")

    @staticmethod
    def _evaluate(args):
        """Runs model according to provided problem file."""
        try:
            api.evaluate_problem(args.conf_file, args.force)
        except FastFileExistsError as exc:
            if _query_yes_no(
                'Output file "%s" already exists. Do you want to overwrite it?' % exc.args[1]
            ):
                api.evaluate_problem(args.conf_file, True)
            else:
                print("Computation not run.")

    @staticmethod
    def _optimize(args):
        """Runs driver according to provided problem file."""
        try:
            api.optimize_problem(args.conf_file, args.force)
        except FastFileExistsError as exc:
            if _query_yes_no(
                'Output file "%s" already exists. Do you want to overwrite it?' % exc.args[1]
            ):
                api.optimize_problem(args.conf_file, True)
            else:
                print("Computation not run.")

    @staticmethod
    def _notebooks(args):
        """Copies the notebook folder in user-selected destination."""
        # Create and copy folder
        target_path = pth.abspath(pth.join(args.path, NOTEBOOK_FOLDER_NAME))
        if pth.exists(target_path):
            shutil.rmtree(target_path)
        os.makedirs(target_path)
        copy_resource_folder("fastoad.notebooks.tutorial", target_path)

        # Give info for running Jupyter
        print("")
        print("Notebooks have been created in %s" % target_path)
        print("You may now run Jupyter with:")
        print('   jupyter notebook "%s"' % target_path)

    # UTILITIES ====================================================================================

    # PARSER CONFIGURATION =========================================================================
    @staticmethod
    def _add_conf_file_argument(parser: ArgumentParser, required=True):
        kwargs = {"type": str, "help": "the configuration file for setting the problem"}
        if not required:
            kwargs["nargs"] = "?"
        parser.add_argument("conf_file", **kwargs)

    @staticmethod
    def _add_overwrite_argument(parser: ArgumentParser):
        parser.add_argument(
            "-f", "--force", action="store_true", help="do not ask before overwriting files"
        )

    # ENTRY POINT ==================================================================================
    def run(self):
        """Main function."""
        subparsers = self.parser.add_subparsers(title="sub-commands")

        # option for version -----------------------------------------------------------------------
        self.parser.add_argument(
            "-v",
            "--version",
            action="version",
            version="FAST-OAD " + fastoad.__version__,
            help="shows version number",
        )

        # sub-command for generating sample configuration file -------------------------------------
        parser_gen_conf = subparsers.add_parser(
            "gen_conf",
            formatter_class=ArgumentDefaultsHelpFormatter,
            help="generates a sample configuration file",
            description="generates the configuration file with sample data",
        )
        parser_gen_conf.help = parser_gen_conf.description
        parser_gen_conf.add_argument(
            "conf_file", type=str, help="the name of configuration file " "to be written"
        )
        self._add_overwrite_argument(parser_gen_conf)
        parser_gen_conf.set_defaults(func=self._generate_conf_file)

        # sub-command for generating input file ----------------------------------------------------
        class _CustomFormatter(RawDescriptionHelpFormatter, ArgumentDefaultsHelpFormatter):
            pass

        parser_gen_inputs = subparsers.add_parser(
            "gen_inputs",
            formatter_class=_CustomFormatter,
            help="generates the input file",
            description="generates the input file (specified in the configuration file)"
            " with needed variables",
        )
        self._add_conf_file_argument(parser_gen_inputs)
        self._add_overwrite_argument(parser_gen_inputs)
        parser_gen_inputs.add_argument(
            "source",
            nargs="?",
            help="if provided, generated input file will be fed with values from provided XML file",
        )
        parser_gen_inputs.add_argument(
            "--legacy",
            action="store_true",
            help="to be used if the source XML file is in legacy format",
        )
        parser_gen_inputs.set_defaults(func=self._generate_inputs)
        parser_gen_inputs.epilog = textwrap.dedent(
            """\
            Examples:
            ---------
            # For the problem defined in conf_file.toml, generates the input file with default 
            # values (when default values are defined):
                %(prog)s gen_inputs conf_file.toml
            
            # Same as above, except that values are taken from some_file.xml when possible:
                %(prog)s gen_inputs conf_file.toml some_file.xml

            # Same as above, some_file.xml is in the legacy FAST schema
                %(prog)s gen_inputs conf_file.toml some_file.xml --legacy
            """
        )

        # sub-command for listing registered systems -----------------------------------------------
        parser_list_systems = subparsers.add_parser(
            "list_systems",
            formatter_class=ArgumentDefaultsHelpFormatter,
            help="Provides the identifiers of available systems",
            description="Provides the identifiers of available systems",
        )
        self._add_conf_file_argument(parser_list_systems, required=False)
        parser_list_systems.set_defaults(func=self._list_systems)

        # sub-command for listing possible outputs -------------------------------------------------
        parser_list_variables = subparsers.add_parser(
            "list_variables",
            formatter_class=ArgumentDefaultsHelpFormatter,
            help="Lists the variables of the problem",
            description="Lists the variables of the problem",
        )
        self._add_conf_file_argument(parser_list_variables)
        parser_list_variables.set_defaults(func=self._list_variables)

        # sub-command for writing N2 diagram -------------------------------------------------------
        parser_n2 = subparsers.add_parser(
            "n2",
            formatter_class=ArgumentDefaultsHelpFormatter,
            help="Writes the N2 diagram of the problem",
            description="Writes an HTML file that shows the N2 diagram of the problem",
        )
        self._add_conf_file_argument(parser_n2)
        self._add_overwrite_argument(parser_n2)
        parser_n2.add_argument(
            "n2_file", nargs="?", default="n2.html", help="path of file to be written"
        )
        parser_n2.set_defaults(func=self._write_n2)

        # sub-command for writing XDSM diagram -------------------------------------------------------
        parser_xdsm = subparsers.add_parser(
            "xdsm",
            formatter_class=ArgumentDefaultsHelpFormatter,
            help="Writes the XDSM diagram of the problem",
            description="Writes an HTML file that shows the XDSM diagram of the problem",
        )
        self._add_conf_file_argument(parser_xdsm)
        self._add_overwrite_argument(parser_xdsm)
        parser_xdsm.add_argument(
            "xdsm_file", nargs="?", default="xdsm.html", help="path of file to be written"
        )
        parser_xdsm.add_argument(
            "--server",
            nargs="?",
            default=None,
            dest="wop_server",
            help="WhatsOpt server URL. Needed only at first call",
        )
        parser_xdsm.add_argument(
            "--depth", nargs="?", default=2, help="Depth of analysis", type=int,
        )
        parser_xdsm.set_defaults(func=self._write_xdsm)

        # sub-command for running the model --------------------------------------------------------
        parser_run_model = subparsers.add_parser(
            "eval",
            formatter_class=ArgumentDefaultsHelpFormatter,
            help="Runs the analysis",
            description="Runs the analysis",
        )
        self._add_conf_file_argument(parser_run_model)
        self._add_overwrite_argument(parser_run_model)
        parser_run_model.set_defaults(func=self._evaluate)

        # sub-command for running the driver -------------------------------------------------------
        parser_run_driver = subparsers.add_parser(
            "optim",
            formatter_class=ArgumentDefaultsHelpFormatter,
            help="Runs the optimization",
            description="Runs the optimization",
        )
        self._add_conf_file_argument(parser_run_driver)
        self._add_overwrite_argument(parser_run_driver)
        parser_run_driver.set_defaults(func=self._optimize)

        # sub-command for running Jupyter notebooks ------------------------------------------------
        parser_notebooks = subparsers.add_parser(
            "notebooks",
            formatter_class=ArgumentDefaultsHelpFormatter,
            help="Create ready-to-use notebooks",
            description="Creates a %s/ folder with pre-configured Jupyter notebooks. "
            "Please note that an existing FAST_OAD_notebooks/ will be erased"
            % NOTEBOOK_FOLDER_NAME,
        )

        parser_notebooks.add_argument(
            "path",
            default=".",
            nargs="?",
            help="The path where the %s/ folder will be added" % NOTEBOOK_FOLDER_NAME,
        )

        parser_notebooks.set_defaults(func=self._notebooks)

        # Parse ------------------------------------------------------------------------------------
        args = self.parser.parse_args()
        try:
            args.func(args)
        except AttributeError:
            self.parser.print_help()


def _query_yes_no(question):
    """
    Ask a yes/no question via input() and return its answer as boolean.

    Keeps asking while answer is not similar to "yes" or "no"
    The returned value is True for "yes" or False for "no".
    """
    answer = None
    while answer is None:
        raw_answer = input(question + "\n")
        try:
            answer = strtobool(raw_answer)
        except ValueError:
            pass

    return answer == 1


def main():
    log_format = "%(levelname)-8s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)
    Main().run()


if __name__ == "__main__":
    main()
