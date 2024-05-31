"""Command Line Interface."""
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

from pathlib import Path

import click
import tabulate

import fastoad
from fastoad.cmd.cli_utils import (
    manage_overwrite,
    out_file_option,
    overwrite_option,
)
from fastoad.cmd.exceptions import FastNoAvailableNotebookError
from fastoad.module_management.exceptions import (
    FastNoAvailableConfigurationFileError,
    FastNoDistPluginError,
    FastSeveralConfigurationFilesError,
    FastSeveralDistPluginsError,
    FastUnknownConfigurationFileError,
    FastUnknownDistPluginError,
    FastNoAvailableSourceDataFileError,
    FastSeveralSourceDataFilesError,
    FastUnknownSourceDataFileError,
)
from . import api

NOTEBOOK_FOLDER_NAME = "FAST-OAD_notebooks"


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(fastoad.__version__, "-v", "--version")
def fast_oad():
    """FAST-OAD main program"""


@fast_oad.command(name="plugin_info")
def plugin_info():
    """Provides list of installed FAST-OAD plugins."""
    api.get_plugin_information(print_data=True)


@fast_oad.command(name="gen_conf")
@click.argument("conf_file", nargs=1)
@click.option(
    "-p",
    "--from_package",
    nargs=1,
    help="Name of installed package that provides the sample configuration file.",
)
@click.option("-s", "--source", nargs=1, help="Name of source configuration file.")
@overwrite_option
def gen_conf(conf_file, from_package, source, force):
    """
    Generate a sample configuration file with given argument as name.

    Option "--from_package" has to be used if several FAST-OAD plugins are available.

    Option "--source_name" has to be used if the targeted plugin provides several sample
    configuration files.

    Use "fastoad plugin_info" to get information about available plugins and sample
    configuration files.
    """
    try:
        manage_overwrite(
            api.generate_configuration_file,
            configuration_file_path=conf_file,
            overwrite=force,
            distribution_name=from_package,
            sample_file_name=source,
        )
    except (
        FastNoDistPluginError,
        FastSeveralDistPluginsError,
        FastUnknownDistPluginError,
        FastSeveralConfigurationFilesError,
        FastUnknownConfigurationFileError,
        FastNoAvailableConfigurationFileError,
    ) as exc:
        click.echo(exc.args[0])


@fast_oad.command(name="gen_source_data_file")
@click.argument("source_data_file", nargs=1)
@click.option(
    "-p",
    "--from_package",
    nargs=1,
    help="Name of installed package that provides the sample source data file.",
)
@click.option("-s", "--source", nargs=1, help="Name of original source data file.")
@overwrite_option
def gen_source_data_file(source_data_file, from_package, source, force):
    """
    Generate a sample source data file with given argument as name.

    Option "--from_package" has to be used if several FAST-OAD plugins are available.

    Option "--source" has to be used if the targeted plugin provides several sample
    source data files.

    Use "fastoad plugin_info" to get information about available plugins and sample
    configuration files.
    """
    try:
        manage_overwrite(
            api.generate_source_data_file,
            source_data_file_path=source_data_file,
            overwrite=force,
            distribution_name=from_package,
            sample_file_name=source,
        )
    except (
        FastNoDistPluginError,
        FastSeveralDistPluginsError,
        FastUnknownDistPluginError,
        FastSeveralSourceDataFilesError,
        FastUnknownSourceDataFileError,
        FastNoAvailableSourceDataFileError,
    ) as exc:
        click.echo(exc.args[0])


@fast_oad.command(name="gen_inputs")
@click.argument("conf_file", nargs=1)
@click.argument("source_data_file", nargs=1, required=False)
@overwrite_option
@click.option(
    "--legacy", is_flag=True, help="To be used if the source data XML file is in legacy format."
)
def gen_inputs(conf_file, source_data_file, force, legacy):
    """
    Generate the input file (specified in the configuration file) with needed variables.

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
    manage_overwrite(
        api.generate_inputs,
        configuration_file_path=conf_file,
        source_data_path=source_data_file,
        source_data_path_schema=schema,
        overwrite=force,
    )


@fast_oad.command(name="list_modules")
@out_file_option
@click.option("-v", "--verbose", is_flag=True, help="Shows detailed information for each system.")
@click.argument("source_path", nargs=-1)
def list_modules(out_file, force, verbose, source_path):
    """
    Provide the identifiers of available systems.

    SOURCE_PATH argument can be a configuration file, or a list of folders where
    custom modules are declared.
    """
    # If a configuration file or a single path is provided make sure it is sent as a
    # string not a list
    if len(source_path) == 1:
        source_path = source_path[0]

    if manage_overwrite(
        api.list_modules,
        source_path=source_path,
        out=out_file,
        overwrite=force,
        verbose=verbose,
    ):
        print("\nDone. Use --verbose (-v) option for detailed information.")


@fast_oad.command(name="list_variables")
@click.argument("conf_file", nargs=1)
@out_file_option
@click.option(
    "--format",
    "table_format",
    default="grid",
    show_default=True,
    help=f"format of the list. Available options are {['var_desc'] + tabulate.tabulate_formats}. "
    '"var_desc" is the variable_descriptions.txt format. Other formats are part of the '
    "tabulate package.",
)
def list_variables(conf_file, out_file, force, table_format):
    """List the variables of the problem defined in CONF_FILE."""
    manage_overwrite(
        api.list_variables,
        configuration_file_path=conf_file,
        out=out_file,
        overwrite=force,
        tablefmt=table_format,
    )


@fast_oad.command(name="n2")
@click.argument("conf_file", nargs=1)
@click.argument("n2_file", nargs=1, default="n2.html", required=False)
@overwrite_option
def write_n2(conf_file, n2_file, force):
    """
    Write an HTML file that shows the N2 diagram of the problem defined in CONF_FILE.

    The name of generated file is `n2.html`, or the given name for argument N2_FILE.
    """
    manage_overwrite(
        api.write_n2,
        configuration_file_path=conf_file,
        n2_file_path=n2_file,
        overwrite=force,
    )


@fast_oad.command(name="xdsm")
@click.argument("conf_file", nargs=1)
@click.argument("xdsm_file", nargs=1, default="xdsm.html", required=False)
@overwrite_option
@click.option("--depth", default=2, show_default=True, help="Depth of analysis.")
@click.option(
    "--server",
    help="URL of WhatsOpt server. For advanced users only.",
)
def write_xdsm(conf_file, xdsm_file, depth, server, force):
    """
    Write an HTML file that shows the XDSM diagram of the problem defined in CONF_FILE.

    The name of generated file is `xdsm.html`, or the given name for argument XDSM_FILE.
    """
    manage_overwrite(
        api.write_xdsm,
        configuration_file_path=conf_file,
        xdsm_file_path=xdsm_file,
        overwrite=force,
        depth=depth,
        wop_server_url=server,
    )


@fast_oad.command(name="eval")
@click.argument("conf_file", nargs=1)
@overwrite_option
def evaluate(conf_file, force):
    """Run the analysis for problem defined in CONF_FILE."""
    manage_overwrite(
        api.evaluate_problem,
        filename_func=lambda pb: pb.output_file_path,
        configuration_file_path=conf_file,
        overwrite=force,
    )


@fast_oad.command(name="optim")
@click.argument("conf_file", nargs=1)
@overwrite_option
def optimize(conf_file, force):
    """Run the optimization for problem defined in CONF_FILE."""
    manage_overwrite(
        api.optimize_problem,
        filename_func=lambda pb: pb.output_file_path,
        configuration_file_path=conf_file,
        overwrite=force,
    )


@fast_oad.command(name="notebooks")
@click.argument("path", nargs=1, default=".", required=False)
@click.option(
    "-p", "--from_package", nargs=1, help="Will use only notebooks from this installed package."
)
def create_notebooks(path, from_package):
    """
    Creates a FAST-OAD_notebooks/ folder with pre-configured Jupyter notebooks.

    If PATH is given, FAST-OAD_notebooks/ will be created in that folder.



    IMPORTANT: Please note that all content of an existing FAST-OAD_notebooks/ will be overwritten.
    """

    root_target_path = Path(path, NOTEBOOK_FOLDER_NAME).absolute()
    try:
        if manage_overwrite(
            api.generate_notebooks,
            destination_path=root_target_path,
            overwrite=False,
            distribution_name=from_package,
        ):
            # Give info for running Jupyter
            click.echo("You may now run Jupyter with:")
            click.echo(f'   jupyter lab "{root_target_path}"')
    except (
        FastNoDistPluginError,
        FastUnknownDistPluginError,
        FastNoAvailableNotebookError,
    ) as exc:
        click.echo(exc.args[0])


if __name__ == "__main__":
    fast_oad()
