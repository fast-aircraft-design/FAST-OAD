"""Command Line Interface."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, RawDescriptionHelpFormatter
from distutils.util import strtobool

import tabulate

import fastoad
from fastoad import notebooks
from fastoad._utils.resource_management.copy import copy_resource_folder
from fastoad.cmd import api
from fastoad.cmd.exceptions import FastFileExistsError

NOTEBOOK_FOLDER_NAME = "FAST-OAD_notebooks"


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
        """Generates a sample configuration file."""
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
    def _list_modules(args):
        """Prints list of system identifiers."""
        # If a configuration file or a single path is provided make sure it is sent as a
        # string not a list
        if len(args.source_path) == 1:
            source_path = args.source_path[0]
        else:
            source_path = args.source_path
        api.list_modules(source_path, out=args.out_file, overwrite=args.force, verbose=args.verbose)
        print("\nDone. Use --verbose (-v) option for detailed information.")

    @staticmethod
    def _list_variables(args):
        """Prints list of system outputs."""
        api.list_variables(
            args.conf_file,
            out=args.out_file,
            overwrite=args.force,
            tablefmt=args.format,
        )

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

        copy_resource_folder(notebooks, target_path)
        # Note: copy_resource_folder(tutorial, target_path) would fail because of IPython imports

        # Give info for running Jupyter
        print("")
        print("Notebooks have been created in %s" % target_path)
        print("You may now run Jupyter with:")
        print('   jupyter lab "%s"' % target_path)

    # UTILITIES ====================================================================================

    # PARSER CONFIGURATION =========================================================================
    @staticmethod
    def _add_conf_file_argument(parser: ArgumentParser, required=True):
        kwargs = {"type": str, "help": "the configuration file for setting the problem"}
        if not required:
            kwargs["nargs"] = "?"
            kwargs["help"] += " (not required)"
        parser.add_argument("conf_file", **kwargs)

    @staticmethod
    def _add_overwrite_argument(parser: ArgumentParser):
        parser.add_argument(
            "-f", "--force", action="store_true", help="do not ask before overwriting files"
        )

    @staticmethod
    def _add_output_file_argument(parser: ArgumentParser):
        parser.add_argument(
            "-o",
            "--out_file",
            type=str,
            help="if provided, command output will be written in indicated file instead of being "
            "printed in terminal.",
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
            help="generates a sample configuration file",
            description="generates the configuration file with sample data",
        )
        parser_gen_conf.help = parser_gen_conf.description
        parser_gen_conf.add_argument(
            "conf_file", type=str, help="the name of configuration file to be written"
        )
        self._add_overwrite_argument(parser_gen_conf)
        parser_gen_conf.set_defaults(func=self._generate_conf_file)

        # sub-command for generating input file ----------------------------------------------------
        parser_gen_inputs = subparsers.add_parser(
            "gen_inputs",
            formatter_class=RawDescriptionHelpFormatter,
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
            # For the problem defined in conf_file.yml, generates the input file with default
            # values (when default values are defined):
                %(prog)s conf_file.yml

            # Same as above, except that values are taken from some_file.xml when possible:
                %(prog)s conf_file.yml some_file.xml

            # Same as above, some_file.xml is in the legacy FAST schema
                %(prog)s conf_file.yml some_file.xml --legacy
            """
        )

        # sub-command for listing registered systems -----------------------------------------------
        parser_list_modules = subparsers.add_parser(
            "list_modules",
            help="Provides the identifiers of available systems",
            description="Provides the identifiers of available systems",
        )
        self._add_output_file_argument(parser_list_modules)
        self._add_overwrite_argument(parser_list_modules)
        parser_list_modules.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="shows detailed information for each system",
        )
        parser_list_modules.add_argument(
            "source_path",
            nargs="*",
            default=None,
            help="either a configuration file path, folder path, or list of folder path",
        )
        parser_list_modules.set_defaults(func=self._list_modules)

        # sub-command for listing problem variables ------------------------------------------------
        parser_list_variables = subparsers.add_parser(
            "list_variables",
            help="Lists the variables of the problem",
            description="Lists the variables of the problem",
        )
        self._add_conf_file_argument(parser_list_variables)
        self._add_output_file_argument(parser_list_variables)
        self._add_overwrite_argument(parser_list_variables)
        parser_list_variables.add_argument(
            "--format",
            nargs="?",
            default="grid",
            help="format of the list. Available options are "
            f"{['var_desc'] + tabulate.tabulate_formats}. "
            '"var_desc" is the variable_descriptions.txt format. Other formats are part of the '
            "tabulate package. (default: %(default)s)",
        )
        parser_list_variables.set_defaults(func=self._list_variables)

        # sub-command for writing N2 diagram -------------------------------------------------------
        parser_n2 = subparsers.add_parser(
            "n2",
            help="Writes the N2 diagram of the problem",
            description="Writes an HTML file that shows the N2 diagram of the problem",
        )
        self._add_conf_file_argument(parser_n2)
        self._add_overwrite_argument(parser_n2)
        parser_n2.add_argument(
            "n2_file",
            nargs="?",
            default="n2.html",
            help="path of file to be written (default: %(default)s)",
        )
        parser_n2.set_defaults(func=self._write_n2)

        # sub-command for writing XDSM diagram -----------------------------------------------------
        parser_xdsm = subparsers.add_parser(
            "xdsm",
            help="Writes the XDSM diagram of the problem",
            description="Writes an HTML file that shows the XDSM diagram of the problem",
        )
        self._add_conf_file_argument(parser_xdsm)
        self._add_overwrite_argument(parser_xdsm)
        parser_xdsm.add_argument(
            "xdsm_file",
            nargs="?",
            default="xdsm.html",
            help="path of file to be written (default: %(default)s)",
        )
        parser_xdsm.add_argument(
            "--depth", nargs="?", default=2, help="Depth of analysis", type=int
        )
        parser_xdsm.add_argument(
            "--server",
            nargs="?",
            default=None,
            dest="wop_server",
            help="URL of WhatsOpt server. For advanced users only.",
        )
        parser_xdsm.set_defaults(func=self._write_xdsm)

        # sub-command for running the model --------------------------------------------------------
        parser_run_model = subparsers.add_parser(
            "eval", help="Runs the analysis", description="Runs the analysis"
        )
        self._add_conf_file_argument(parser_run_model)
        self._add_overwrite_argument(parser_run_model)
        parser_run_model.set_defaults(func=self._evaluate)

        # sub-command for running the driver -------------------------------------------------------
        parser_run_driver = subparsers.add_parser(
            "optim", help="Runs the optimization", description="Runs the optimization"
        )
        self._add_conf_file_argument(parser_run_driver)
        self._add_overwrite_argument(parser_run_driver)
        parser_run_driver.set_defaults(func=self._optimize)

        # sub-command for running Jupyter notebooks ------------------------------------------------
        parser_notebooks = subparsers.add_parser(
            "notebooks",
            help="Create ready-to-use notebooks",
            description="Creates a %(nb_folder)s/ folder with pre-configured Jupyter notebooks. "
            "Please note that all content of an existing %(nb_folder)s/ will be overwritten."
            % {"nb_folder": NOTEBOOK_FOLDER_NAME},
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
        args.func(args)


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
