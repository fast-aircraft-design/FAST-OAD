"""
API
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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
import os.path as pth
import sys
import textwrap as tw
from collections.abc import Iterable
from time import time
from typing import IO, List, Union

import openmdao.api as om
from IPython import InteractiveShell
from IPython.display import HTML, clear_output, display
from tabulate import tabulate

import fastoad.openmdao.whatsopt
from fastoad._utils.files import make_parent_dir
from fastoad._utils.resource_management.copy import copy_resource
from fastoad.cmd.exceptions import (
    FastFileExistsError,
    FastSeveralConfigurationFilesError,
    FastSeveralPluginsError,
    FastUnknownConfigurationFileError,
    FastUnknownPluginError,
)
from fastoad.gui import OptimizationViewer, VariableViewer
from fastoad.io import IVariableIOFormatter
from fastoad.io.configuration import FASTOADProblemConfigurator
from fastoad.io.variable_io import DataFile
from fastoad.io.xml import VariableLegacy1XmlFormatter
from fastoad.module_management._bundle_loader import BundleLoader
from fastoad.module_management._plugins import FastoadLoader
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem, RegisterPropulsion
from fastoad.openmdao.problem import FASTOADProblem
from fastoad.openmdao.variables import VariableList

# from . import resources

DEFAULT_WOP_URL = "https://ether.onera.fr/whatsopt"
_LOGGER = logging.getLogger(__name__)

SAMPLE_FILENAME = "fastoad.yml"
MAX_TABLE_WIDTH = 200  # For variable list text output

# Used for test purposes only
_PROBLEM_CONFIGURATOR = None


def generate_configuration_file(
    configuration_file_path: str,
    overwrite: bool = False,
    distribution_name=None,
    sample_file_name=None,
):
    """
    Generates a sample configuration file.

    :param configuration_file_path: the path of file to be written
    :param overwrite: if True, the file will be written, even if it already exists
    :param distribution_name: the name of the Python library that provides the sample configuration
                             file (can be omitted if only one plugin is available)
    :param sample_file_name: the name of the sample configuration file (can be omitted if
                             the plugin provides only one configuration file)
    :return: path of generated file
    :raise FastFileExistsError: if overwrite==False and configuration_file_path already exists
    :raise FastSeveralPluginsError: if several plugins are available but `plugin_name` has not
                                    been provided
    :raise FastUnknownPluginError: if the specified plugin is not available
    :raise FastSeveralConfigurationFilesError: if the specified plugin provides several sample
                                               configuration files but `sample_configuration_file`
                                               has not been provided
    :raise FastUnknownConfigurationFileError: if the specified plugin does not provide specified
                                              configuration file
    """
    configuration_file_path = pth.abspath(configuration_file_path)
    if not overwrite and pth.exists(configuration_file_path):
        raise FastFileExistsError(
            f"Configuration file {configuration_file_path} not written because it already exists. "
            "Use overwrite=True to bypass.",
            configuration_file_path,
        )

    make_parent_dir(configuration_file_path)

    loader = FastoadLoader()
    plugin_definitions = loader.plugin_definitions
    if distribution_name is None:
        if len(plugin_definitions) == 1:
            distribution_name = next(iter(plugin_definitions.keys()))
        else:
            raise FastSeveralPluginsError()

    if distribution_name not in plugin_definitions:
        raise FastUnknownPluginError(distribution_name)

    conf_file_list = loader.get_configuration_file_list(distribution_name)
    if sample_file_name is None:
        if len(conf_file_list) > 1:
            raise FastSeveralConfigurationFilesError(distribution_name)
        else:
            sample_file_name, plugin_name = conf_file_list[0]
    else:
        matching_list = list(filter(lambda item: item[0] == sample_file_name, conf_file_list))
        if len(matching_list) == 0:
            raise FastUnknownConfigurationFileError(sample_file_name, distribution_name)
        plugin_name = matching_list[0][1]

        if plugin_name is None:
            raise FastUnknownConfigurationFileError(sample_file_name, distribution_name)

    configuration_package = plugin_definitions[distribution_name][plugin_name].subpackages[
        "configurations"
    ]
    copy_resource(configuration_package, sample_file_name, configuration_file_path)
    _LOGGER.info(f"Sample configuration written in {configuration_file_path}")
    return configuration_file_path


def generate_inputs(
    configuration_file_path: str,
    source_path: str = None,
    source_path_schema="native",
    overwrite: bool = False,
) -> str:
    """
    Generates input file for the problem specified in configuration_file_path.

    :param configuration_file_path: where the path of input file to write is set
    :param source_path: path of file data will be taken from
    :param source_path_schema: set to 'legacy' if the source file come from legacy FAST
    :param overwrite: if True, file will be written even if one already exists
    :return: path of generated file
    :raise FastFileExistsError: if overwrite==False and configuration_file_path already exists
    """
    conf = FASTOADProblemConfigurator(configuration_file_path)
    conf._set_configuration_modifier(_PROBLEM_CONFIGURATOR)

    input_file_path = conf.input_file_path
    if not overwrite and pth.exists(conf.input_file_path):
        raise FastFileExistsError(
            "Input file %s not written because it already exists. "
            "Use overwrite=True to bypass." % input_file_path,
            input_file_path,
        )

    if source_path_schema == "legacy":
        conf.write_needed_inputs(source_path, VariableLegacy1XmlFormatter())
    else:
        conf.write_needed_inputs(source_path)

    _LOGGER.info("Problem inputs written in %s", input_file_path)
    return input_file_path


def list_variables(
    configuration_file_path: str,
    out: Union[IO, str] = None,
    overwrite: bool = False,
    force_text_output: bool = False,
    tablefmt: str = "grid",
):
    """
    Writes list of variables for the problem specified in configuration_file_path.

    List is generally written as text. It can be displayed as a scrollable table view if:
    - function is used in an interactive IPython shell
    - out == sys.stdout
    - force_text_output == False

    :param configuration_file_path:
    :param out: the output stream or a path for the output file (None means sys.stdout)
    :param overwrite: if True and out parameter is a file path, the file will be written even if one
                      already exists
    :param force_text_output: if True, list will be written as text, even if command is used in an
                              interactive IPython shell (Jupyter notebook). Has no effect in other
                              shells or if out parameter is not sys.stdout
    :param tablefmt: The formatting of the requested table. Options are the same as those available
                     to the tabulate package. See tabulate.tabulate_formats for a complete list.
                     If "var_desc" the file will use the variable_descriptions.txt format.
    :return: path of generated file, or None if no file was generated.
    :raise FastFileExistsError: if `overwrite==False` and `out` is a file path and the file exists
    """
    if out is None:
        out = sys.stdout

    conf = FASTOADProblemConfigurator(configuration_file_path)
    conf._set_configuration_modifier(_PROBLEM_CONFIGURATOR)
    problem = conf.get_problem()
    problem.setup()

    # Extracting inputs and outputs
    variables = VariableList.from_problem(problem)
    variables.sort(key=lambda var: var.name)
    input_variables = VariableList([var for var in variables if var.is_input])
    output_variables = VariableList([var for var in variables if not var.is_input])

    for var in input_variables:
        var.metadata["I/O"] = "IN"
    for var in output_variables:
        var.metadata["I/O"] = "OUT"

    variables_df = (
        (input_variables + output_variables)
        .to_dataframe()[["name", "I/O", "desc"]]
        .rename(columns={"name": "NAME", "desc": "DESCRIPTION"})
    )

    if isinstance(out, str):
        out = pth.abspath(out)
        if not overwrite and pth.exists(out):
            raise FastFileExistsError(
                "File %s not written because it already exists. "
                "Use overwrite=True to bypass." % out,
                out,
            )
        make_parent_dir(out)
        out_file = open(out, "w")
    else:
        if out == sys.stdout and InteractiveShell.initialized() and not force_text_output:
            display(HTML(variables_df.to_html(index=False)))
            return None

        # Here we continue with text output
        out_file = out

    if tablefmt == "var_desc":
        content = _generate_var_desc_format(variables_df)
    else:
        content = _generate_table_format(variables_df, tablefmt=tablefmt)

    out_file.write(content)

    if isinstance(out, str):
        out_file.close()
        _LOGGER.info("Output list written in %s", out)
        return out

    return None


def _generate_var_desc_format(variables_df):
    content = variables_df.to_csv(
        columns=["NAME", "DESCRIPTION"],
        sep="|",
        index=False,
        header=False,
        line_terminator="\n",
    ).replace("|", " || ")
    return content


def _generate_table_format(variables_df, tablefmt="grid"):
    # Break descriptions that are too long
    variables_df["DESCRIPTION"] = variables_df["DESCRIPTION"].apply(
        lambda s: "\n".join(tw.wrap(s, 100))
    )
    content = tabulate(
        variables_df, headers=variables_df.columns, showindex=False, tablefmt=tablefmt
    )
    return content + "\n"


def list_modules(
    source_path: Union[List[str], str] = None,
    out: Union[IO, str] = None,
    overwrite: bool = False,
    verbose: bool = False,
    force_text_output: bool = False,
):
    """
    Writes list of available systems.
    If source_path is given and if it defines paths where there are registered systems,
    they will be listed too.

    :param source_path: either a configuration file path, folder path, or list of folder path
    :param out: the output stream or a path for the output file (None means sys.stdout)
    :param overwrite: if True and out is a file path, the file will be written even if one already
                      exists
    :param verbose: if True, shows detailed information for each system
                    if False, shows only identifier and path of each system
    :param force_text_output: if True, list will be written as text, even if command is used in an
                              interactive IPython shell (Jupyter notebook). Has no effect in other
                              shells or if out parameter is not sys.stdout
    :return: path of generated file, or None if no file was generated.
    :raise FastFileExistsError: if `overwrite==False` and `out` is a file path and the file exists
    """
    if out is None:
        out = sys.stdout

    if isinstance(source_path, str):
        if pth.isfile(source_path):
            conf = FASTOADProblemConfigurator(source_path)
            conf._set_configuration_modifier(_PROBLEM_CONFIGURATOR)
            # As the problem has been configured,
            # BundleLoader now knows additional registered systems
        elif pth.isdir(source_path):
            RegisterOpenMDAOSystem.explore_folder(source_path)
        else:
            raise FileNotFoundError("Could not find %s" % source_path)
    elif isinstance(source_path, Iterable):
        for folder_path in source_path:
            if not pth.isdir(folder_path):
                _LOGGER.warning("SKIPPED %s: folder does not exist.", folder_path)
            else:
                RegisterOpenMDAOSystem.explore_folder(folder_path)
    elif source_path is not None:
        raise RuntimeError("Unexpected type for source_path")

    if verbose:
        cell_list = _get_detailed_system_list()
    else:
        cell_list = _get_simple_system_list()

    if isinstance(out, str):
        out = pth.abspath(out)
        if not overwrite and pth.exists(out):
            raise FastFileExistsError(
                "File %s not written because it already exists. "
                "Use overwrite=True to bypass." % out,
                out,
            )

        make_parent_dir(out)
        out_file = open(out, "w")
    else:
        if (
            out == sys.stdout
            and InteractiveShell.initialized()
            and not force_text_output
            and not verbose
        ):
            display(HTML(tabulate(cell_list, tablefmt="html")))
            return None

        out_file = out

    out_file.write(tabulate(cell_list, tablefmt="grid"))
    out_file.write("\n")

    if isinstance(out, str):
        out_file.close()
        _LOGGER.info("System list written in %s", out)
        return out

    return None


def _get_simple_system_list():
    cell_list = [["   AVAILABLE MODULE IDENTIFIERS", "MODULE PATH"]]
    for identifier in sorted(RegisterOpenMDAOSystem.get_provider_ids()):
        path = BundleLoader().get_factory_path(identifier)
        cell_list.append([identifier, path])

    cell_list.append(["   AVAILABLE PROPULSION WRAPPER IDENTIFIERS", "MODULE PATH"])
    for identifier in sorted(RegisterPropulsion.get_provider_ids()):
        path = BundleLoader().get_factory_path(identifier)
        cell_list.append([identifier, path])

    return cell_list


def _get_detailed_system_list():
    cell_list = [["AVAILABLE MODULE IDENTIFIERS\n============================"]]
    for identifier in sorted(RegisterOpenMDAOSystem.get_provider_ids()):
        path = BundleLoader().get_factory_path(identifier)
        domain = RegisterOpenMDAOSystem.get_provider_domain(identifier)
        description = RegisterOpenMDAOSystem.get_provider_description(identifier)
        if description is None:
            description = ""

        # We remove OpenMDAO's native options from the description
        component = RegisterOpenMDAOSystem.get_system(identifier)
        component.options.undeclare("assembled_jac_type")
        component.options.undeclare("distributed")

        cell_content = (
            "  IDENTIFIER:   %s\nPATH:         %s\nDOMAIN:       %s\nDESCRIPTION:  %s\n"
            % (identifier, path, domain.value, tw.indent(tw.dedent(description), "    "))
        )
        if len(list(component.options.items())) > 0:
            cell_content += component.options.to_table(fmt="grid") + "\n"

        cell_list.append([cell_content])
    cell_list.append(
        ["AVAILABLE PROPULSION WRAPPER IDENTIFIERS\n========================================"]
    )
    for identifier in sorted(RegisterPropulsion.get_provider_ids()):
        path = BundleLoader().get_factory_path(identifier)
        description = RegisterPropulsion.get_provider_description(identifier)
        if description is None:
            description = ""

        cell_content = "  IDENTIFIER:   %s\nPATH:         %s\nDESCRIPTION:  %s\n" % (
            identifier,
            path,
            tw.indent(tw.dedent(description), "    "),
        )
        cell_list.append([cell_content])
    return cell_list


def write_n2(configuration_file_path: str, n2_file_path: str = None, overwrite: bool = False):
    """
    Write the N2 diagram of the problem in file n2.html

    :param configuration_file_path:
    :param n2_file_path: if None, will default to `n2.html`
    :param overwrite:
    :return: path of generated file.
    :raise FastFileExistsError: if overwrite==False and n2_file_path already exists
    """

    if not n2_file_path:
        n2_file_path = "n2.html"
    n2_file_path = pth.abspath(n2_file_path)

    if not overwrite and pth.exists(n2_file_path):
        raise FastFileExistsError(
            "N2-diagram file %s not written because it already exists. "
            "Use overwrite=True to bypass." % n2_file_path,
            n2_file_path,
        )

    make_parent_dir(n2_file_path)
    conf = FASTOADProblemConfigurator(configuration_file_path)
    conf._set_configuration_modifier(_PROBLEM_CONFIGURATOR)
    problem = conf.get_problem()
    problem.setup()
    problem.final_setup()

    om.n2(problem, outfile=n2_file_path, show_browser=False)
    if InteractiveShell.initialized():
        clear_output()
    _LOGGER.info("N2 diagram written in %s", pth.abspath(n2_file_path))
    return n2_file_path


def write_xdsm(
    configuration_file_path: str,
    xdsm_file_path: str = None,
    overwrite: bool = False,
    depth: int = 2,
    wop_server_url: str = None,
    dry_run: bool = False,
):
    """

    :param configuration_file_path:
    :param xdsm_file_path: the path for HTML file to be written (will overwrite if needed)
    :param overwrite: if False, will raise an error if file already exists.
    :param depth: the depth analysis for WhatsOpt
    :param wop_server_url: URL of WhatsOpt server (if None, ether.onera.fr/whatsopt will be used)
    :param dry_run: if True, will run wop without sending any request to the server. Generated
                    XDSM will be empty. (for test purpose only)
    :return: path of generated file.
    :raise FastFileExistsError: if overwrite==False and xdsm_file_path already exists
    """
    if not xdsm_file_path:
        xdsm_file_path = pth.join(pth.dirname(configuration_file_path), "xdsm.html")
    xdsm_file_path = pth.abspath(xdsm_file_path)

    if not overwrite and pth.exists(xdsm_file_path):
        raise FastFileExistsError(
            "XDSM-diagram file %s not written because it already exists. "
            "Use overwrite=True to bypass." % xdsm_file_path,
            xdsm_file_path,
        )

    make_parent_dir(xdsm_file_path)

    conf = FASTOADProblemConfigurator(configuration_file_path)
    conf._set_configuration_modifier(_PROBLEM_CONFIGURATOR)
    problem = conf.get_problem()
    problem.setup()
    problem.final_setup()

    fastoad.openmdao.whatsopt.write_xdsm(problem, xdsm_file_path, depth, wop_server_url, dry_run)
    return xdsm_file_path


def _run_problem(
    configuration_file_path: str,
    overwrite: bool = False,
    mode="run_model",
    auto_scaling: bool = False,
) -> FASTOADProblem:
    """
    Runs problem according to provided file

    :param configuration_file_path: problem definition
    :param overwrite: if True, output file will be overwritten
    :param mode: 'run_model' or 'run_driver'
    :param auto_scaling: if True, automatic scaling is performed for design variables and
                         constraints
    :return: the OpenMDAO problem after run
    :raise FastFileExistsError: if overwrite==False and output data file of problem already exists
    """

    conf = FASTOADProblemConfigurator(configuration_file_path)
    conf._set_configuration_modifier(_PROBLEM_CONFIGURATOR)
    problem = conf.get_problem(read_inputs=True, auto_scaling=auto_scaling)

    outputs_path = pth.normpath(problem.output_file_path)
    if not overwrite and pth.exists(outputs_path):
        raise FastFileExistsError(
            "Problem not run because output file %s already exists. "
            "Use overwrite=True to bypass." % outputs_path,
            outputs_path,
        )

    problem.setup()
    start_time = time()
    if mode == "run_model":
        problem.run_model()
        problem.optim_failed = False  # Actually, we don't know
    else:
        problem.optim_failed = problem.run_driver()
    end_time = time()
    computation_time = round(end_time - start_time, 2)

    problem.write_outputs()
    if problem.optim_failed:
        _LOGGER.error("Optimization failed after " + str(computation_time) + " seconds")
    else:
        _LOGGER.info("Computation finished after " + str(computation_time) + " seconds")

    _LOGGER.info("Problem outputs written in %s", outputs_path)

    return problem


def evaluate_problem(configuration_file_path: str, overwrite: bool = False) -> FASTOADProblem:
    """
    Runs model according to provided problem file

    :param configuration_file_path: problem definition
    :param overwrite: if True, output file will be overwritten
    :return: the OpenMDAO problem after run
    :raise FastFileExistsError: if overwrite==False and output data file of problem already exists
    """
    return _run_problem(configuration_file_path, overwrite, "run_model")


def optimize_problem(
    configuration_file_path: str, overwrite: bool = False, auto_scaling: bool = False
) -> FASTOADProblem:
    """
    Runs driver according to provided problem file

    :param configuration_file_path: problem definition
    :param overwrite: if True, output file will be overwritten
    :param auto_scaling: if True, automatic scaling is performed for design variables and
                         constraints
    :return: the OpenMDAO problem after run
    :raise FastFileExistsError: if overwrite==False and output data file of problem already exists
    """
    return _run_problem(configuration_file_path, overwrite, "run_driver", auto_scaling=auto_scaling)


def optimization_viewer(configuration_file_path: str):
    """
    Displays optimization information and enables its editing

    :param configuration_file_path: problem definition
    :return: display of the OptimizationViewer
    """
    conf = FASTOADProblemConfigurator(configuration_file_path)
    conf._set_configuration_modifier(_PROBLEM_CONFIGURATOR)
    viewer = OptimizationViewer()
    viewer.load(conf)

    return viewer.display()


def variable_viewer(file_path: str, file_formatter: IVariableIOFormatter = None, editable=True):
    """
    Displays a widget that enables to visualize variables information and edit their values.

    :param file_path: the path of file to interact with
    :param file_formatter: the formatter that defines file format. If not provided, default format
                           will be assumed.
    :param editable: if True, an editable table with variable filters will be displayed. If False,
                     the table will not be editable nor searchable, but can be stored in an HTML
                     file.
    :return: display handle of the VariableViewer
    """
    if editable:
        viewer = VariableViewer()
        viewer.load(file_path, file_formatter)

        handle = viewer.display()
    else:
        variables = DataFile(file_path, formatter=file_formatter)
        variables.sort(key=lambda var: var.name)

        table = variables.to_dataframe()[["name", "val", "units", "is_input", "desc"]].rename(
            columns={"name": "Name", "val": "Value", "units": "Unit", "desc": "Description"}
        )
        table["I/O"] = "OUT"
        table["I/O"].loc[table["is_input"]] = "IN"
        del table["is_input"]
        table.set_index("Name", drop=True, inplace=True)

        handle = display(HTML(table.to_html()))
    return handle
