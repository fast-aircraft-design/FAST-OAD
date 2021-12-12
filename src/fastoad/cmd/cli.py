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
from distutils.util import strtobool

import click
import tabulate

import fastoad
from fastoad import api
from fastoad.cmd.exceptions import FastFileExistsError


@click.group(
    context_settings=dict(
        help_option_names=["-h", "--help"],
    )
)
@click.version_option(fastoad.__version__, "-v", "--version")
def fast_oad():
    """FAST-OAD main program"""


def fast_oad_subcommand(func):
    """Decorator for adding a command as subcommand to `fast_oad`."""
    return fast_oad.add_command(func)


def overwrite_option(func):
    """
    Decorator for adding the option for overwriting existing file.

    Use `force` as argument of the function.
    """
    return click.option(
        "-f",
        "--force",
        is_flag=True,
        help="Do not ask before overwriting files.",
    )(func)


def out_file_option(func):
    """
    Decorator for writing command output in a file.

    Use `out_file` and `force` as argument of the function.
    """
    return click.option(
        "-o",
        "--out_file",
        help="If provided, command output will be written in indicated file instead of "
        "being printed in terminal.",
    )(overwrite_option(func))


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


@fast_oad_subcommand
@click.command(name="gen_conf")
@click.argument("conf_file", nargs=1)
@overwrite_option
def gen_conf(conf_file, force):
    """Generates a sample configuration file with given argument as name."""
    try:
        api.generate_configuration_file(conf_file, overwrite=force)
    except FastFileExistsError:
        if _query_yes_no(
            f"Configuration file {conf_file} already exists. Do you want to overwrite it?"
        ):
            api.generate_configuration_file(conf_file, overwrite=True)
        else:
            print("No file written.")


@fast_oad_subcommand
@click.command(name="gen_inputs")
@click.argument("conf_file", nargs=1)
@click.argument("source_file", nargs=1, required=False)
@overwrite_option
@click.option(
    "--legacy", is_flag=True, help="To be used if the source XML file is in legacy format."
)
def gen_inputs(conf_file, source_file, force, legacy):
    """
    Generates the input file (specified in the configuration file) with needed variables.

    \b
    Examples:
    ---------
    # For the problem defined in conf_file.yml, generates the input file with default
    # values (when default values are defined):
        fastoad gen_inputs conf_file.yml

    \b
    # Same as above, except that values are taken from some_file.xml when possible:
        fastoad gen_inputs conf_file.yml some_file.xml

    \b
    # Same as above, some_file.xml is formatted with the legacy FAST schema
        fastoad gen_inputs conf_file.yml some_file.xml --legacy
    """
    schema = "legacy" if legacy else "native"
    try:
        api.generate_inputs(conf_file, source_file, schema, overwrite=force)
    except FastFileExistsError as exc:
        if _query_yes_no(f"Input file {exc.args[1]} already exists. Do you want to overwrite it?"):
            api.generate_inputs(conf_file, source_file, schema, overwrite=True)
        else:
            print("No file written.")


@fast_oad_subcommand
@click.command(name="list_modules")
@out_file_option
@click.option("-v", "--verbose", is_flag=True, help="Shows detailed information for each system.")
@click.argument("source_path", nargs=-1)
def list_modules(out_file, force, verbose, source_path):
    """
    Provides the identifiers of available systems.

    SOURCE_PATH argument can be a configuration file, or a list of folders where
    custom modules are declared.
    """
    # If a configuration file or a single path is provided make sure it is sent as a
    # string not a list
    if len(source_path) == 1:
        source_path = source_path[0]
    try:
        api.list_modules(source_path, out=out_file, overwrite=force, verbose=verbose)
    except FastFileExistsError:
        if _query_yes_no(f"Output file {out_file} already exists. Do you want to overwrite it?"):
            api.list_modules(source_path, out=out_file, overwrite=True, verbose=verbose)
        else:
            print("No file written.")

    print("\nDone. Use --verbose (-v) option for detailed information.")


@fast_oad_subcommand
@click.command(name="list_variables")
@click.argument("conf_file", nargs=1)
@out_file_option
@click.option(
    "--format",
    default="grid",
    show_default=True,
    help=f"format of the list. Available options are {['var_desc'] + tabulate.tabulate_formats}. "
    '"var_desc" is the variable_descriptions.txt format. Other formats are part of the '
    "tabulate package.",
)
def list_variables(conf_file, out_file, force, format):
    """Lists the variables of the problem."""
    try:
        api.list_variables(conf_file, out=out_file, overwrite=force, tablefmt=format)
    except FastFileExistsError:
        if _query_yes_no(f"Output file {out_file} already exists. Do you want to overwrite it?"):
            api.list_variables(conf_file, out=out_file, overwrite=True, tablefmt=format)
        else:
            print("No file written.")


@fast_oad_subcommand
@click.command()
def n2():
    """Writes the N2 diagram of the problem"""
    pass


@fast_oad_subcommand
@click.command()
def xdsm():
    """Writes the XDSM diagram of the problem"""
    pass


@fast_oad_subcommand
@click.command()
def eval():
    """Runs the analysis"""
    pass


@fast_oad_subcommand
@click.command()
def optim():
    """Runs the optimization"""
    pass


@fast_oad_subcommand
@click.command()
def notebooks():
    """Creates ready-to-use notebooks"""
    pass


if __name__ == "__main__":
    fast_oad()
