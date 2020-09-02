"""
API
"""
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
import os.path as pth
import sys
import textwrap as tw
from shutil import get_terminal_size
from typing import IO, Union

import numpy as np
import openmdao.api as om
import pandas as pd
import requests
from IPython import InteractiveShell
from IPython.display import display, HTML
from whatsopt.show_utils import generate_xdsm_html
from whatsopt.whatsopt_client import WhatsOpt, PROD_URL

from fastoad.cmd.exceptions import FastFileExistsError
from fastoad.io.configuration import FASTOADProblem
from fastoad.io.configuration.configuration import FASTOADProblemConfigurator
from fastoad.io.xml import VariableLegacy1XmlFormatter
from fastoad.module_management import BundleLoader
from fastoad.module_management import OpenMDAOSystemRegistry
from fastoad.openmdao.variables import VariableList
from fastoad.utils.files import make_parent_dir
from fastoad.utils.postprocessing import OptimizationViewer
from fastoad.utils.resource_management.copy import copy_resource
from . import resources

# Logger for this module
from ..module_management.service_registry import RegisterPropulsion

DEFAULT_WOP_URL = "https://ether.onera.fr/whatsopt"
_LOGGER = logging.getLogger(__name__)

SAMPLE_FILENAME = "fastoad.toml"
MAX_TABLE_WIDTH = 200  # For variable list text output


def generate_configuration_file(configuration_file_path: str, overwrite: bool = False):
    """
    Generates a sample configuration file.

    :param configuration_file_path: the path of file to be written
    :param overwrite: if True, the file will be written, even if it already exists
    :raise FastFileExistsError: if overwrite==False and configuration_file_path already exists
    """
    if not overwrite and pth.exists(configuration_file_path):
        raise FastFileExistsError(
            "Configuration file %s not written because it already exists. "
            "Use overwrite=True to bypass." % configuration_file_path,
            configuration_file_path,
        )

    make_parent_dir(configuration_file_path)

    copy_resource(resources, SAMPLE_FILENAME, configuration_file_path)
    _LOGGER.info("Sample configuration written in %s", configuration_file_path)


def generate_inputs(
    configuration_file_path: str,
    source_path: str = None,
    source_path_schema="native",
    overwrite: bool = False,
):
    """
    Generates input file for the :class:`FASTOADProblem` specified in configuration_file_path.

    :param configuration_file_path: where the path of input file to write is set
    :param source_path: path of file data will be taken from
    :param source_path_schema: set to 'legacy' if the source file come from legacy FAST
    :param overwrite: if True, file will be written even if one already exists
    :raise FastFileExistsError: if overwrite==False and configuration_file_path already exists
    """
    conf = FASTOADProblemConfigurator(configuration_file_path)

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


def list_variables(
    configuration_file_path: str,
    out: Union[IO, str] = sys.stdout,
    overwrite: bool = False,
    force_text_output: bool = False,
):
    """
    Writes list of system outputs for the :class:`FASTOADProblem` specified in configuration_file_path.

    List is generally written as text. It can be displayed as a scrollable table view if:
    - function is used in an interactive IPython shell
    - out == sys.stdout
    - force_text_output == False

    :param configuration_file_path:
    :param out: the output stream or a path for the output file
    :param overwrite: if True and out parameter is a file path, the file will be written even if one already
                      exists
    :param force_text_output: if True, list will be written as text, even if command is used in an interactive IPython
                              shell (Jupyter notebook). Has no effect in other shells or if out parameter is not
                              sys.stdout
    :raise FastFileExistsError: if overwrite==False and out parameter is a file path and the file exists
    """
    conf = FASTOADProblemConfigurator(configuration_file_path)
    problem = conf.get_problem()

    # Extracting inputs and outputs
    variables = VariableList.from_problem(problem, promoted_only=False)
    variables.sort(key=lambda var: var.name)
    input_variables = VariableList([var for var in variables if var.is_input])
    output_variables = VariableList([var for var in variables if not var.is_input])

    if isinstance(out, str):
        if not overwrite and pth.exists(out):
            raise FastFileExistsError(
                "File %s not written because it already exists. "
                "Use overwrite=True to bypass." % out,
                out,
            )
        make_parent_dir(out)
        out_file = open(out, "w")
        table_width = MAX_TABLE_WIDTH
    else:
        if out == sys.stdout and InteractiveShell.initialized() and not force_text_output:
            # Here we display the variable list as VariableViewer in a notebook
            for var in input_variables:
                var.metadata["I/O"] = "IN"
            for var in output_variables:
                var.metadata["I/O"] = "OUT"

            df = (
                (input_variables + output_variables)
                .to_dataframe()[["I/O", "name", "desc"]]
                .rename(columns={"name": "Name", "desc": "Description"})
            )
            display(HTML(df.to_html()))
            return

        # Here we continue with text output
        out_file = out
        table_width = min(get_terminal_size().columns, MAX_TABLE_WIDTH) - 1

    pd.set_option("display.max_colwidth", 1000)
    max_name_length = np.max(
        [len(name) for name in input_variables.names() + output_variables.names()]
    )
    description_text_width = table_width - max_name_length - 2

    def _write_variables(out_f, variables):
        """Writes variables and their description as a pandas DataFrame"""
        df = variables.to_dataframe()

        # Create a new Series where description are wrapped on several lines if needed.
        # Each line becomes an element of the Series
        df["desc"] = ["\n".join(tw.wrap(s, description_text_width)) for s in df["desc"]]
        new_desc = df.desc.str.split("\n", expand=True).stack()

        # Create a Series for name that will match new_desc Series. Variable name will be in front of
        # first line of description. An empty string will be in front of other lines.
        new_name = [df.name.loc[i] if j == 0 else "" for i, j in new_desc.index]

        # Create the DataFrame that will be displayed
        new_df = pd.DataFrame({"NAME": new_name, "DESCRIPTION": new_desc})

        out_f.write(
            new_df.to_string(
                index=False,
                columns=["NAME", "DESCRIPTION"],
                justify="center",
                formatters={  # Formatters are needed for enforcing left justification
                    "NAME": ("{:%s}" % max_name_length).format,
                    "DESCRIPTION": ("{:%s}" % description_text_width).format,
                },
            )
        )
        out_file.write("\n")

    def _write_text_with_line(txt: str, line_length: int):
        """ Writes a line of given length with provided text inside """
        out_file.write("-" + txt + "-" * (line_length - 1 - len(txt)) + "\n")

    # Inputs
    _write_text_with_line(" INPUTS OF THE PROBLEM ", table_width)
    _write_variables(out_file, input_variables)

    # Outputs
    out_file.write("\n")
    _write_text_with_line(" OUTPUTS OF THE PROBLEM ", table_width)
    _write_variables(out_file, output_variables)
    _write_text_with_line("", table_width)

    if isinstance(out, str):
        out_file.close()
        _LOGGER.info("Output list written in %s", out_file)


def list_systems(
    configuration_file_path: str = None, out: Union[IO, str] = sys.stdout, overwrite: bool = False
):
    """
    Writes list of available systems.
    If configuration_file_path is given and if it defines paths where there are registered systems,
    they will be listed too.

    :param configuration_file_path:
    :param out: the output stream or a path for the output file
    :param overwrite: if True and out is a file path, the file will be written even if one already
                      exists
    :raise FastFileExistsError: if overwrite==False and out is a file path and the file exists
    """

    if configuration_file_path:
        conf = FASTOADProblemConfigurator(configuration_file_path)
        conf.load(configuration_file_path)
    # As the problem has been configured, BundleLoader now knows additional registered systems

    if isinstance(out, str):
        if not overwrite and pth.exists(out):
            raise FastFileExistsError(
                "File %s not written because it already exists. "
                "Use overwrite=True to bypass." % out,
                out,
            )

        make_parent_dir(out)
        out_file = open(out, "w")
    else:
        out_file = out
    out_file.writelines(["== AVAILABLE SYSTEM IDENTIFIERS " + "=" * 68 + "\n", "-" * 100 + "\n"])
    for identifier in sorted(OpenMDAOSystemRegistry.get_system_ids()):
        path = BundleLoader().get_factory_path(identifier)
        domain = OpenMDAOSystemRegistry.get_system_domain(identifier)
        description = OpenMDAOSystemRegistry.get_system_description(identifier)
        if description is None:
            description = ""
        out_file.write("  IDENTIFIER:   %s\n" % identifier)
        out_file.write("  PATH:         %s\n" % path)
        out_file.write("  DOMAIN:       %s\n" % domain.value)
        out_file.write("  DESCRIPTION:  %s\n" % tw.indent(tw.dedent(description), "    "))
        out_file.write("-" * 100 + "\n")
    out_file.write("=" * 100 + "\n")

    out_file.writelines(
        ["\n== AVAILABLE PROPULSION WRAPPER IDENTIFIERS " + "=" * 56 + "\n", "-" * 100 + "\n"]
    )
    for identifier in sorted(RegisterPropulsion.get_model_ids()):
        path = BundleLoader().get_factory_path(identifier)
        description = RegisterPropulsion.get_service_description(identifier)
        if description is None:
            description = ""
        out_file.write("  IDENTIFIER:   %s\n" % identifier)
        out_file.write("  PATH:         %s\n" % path)
        out_file.write("  DESCRIPTION:  %s\n" % tw.indent(tw.dedent(description), "    "))
        out_file.write("-" * 100 + "\n")
    out_file.write("=" * 100 + "\n")

    if isinstance(out, str):
        out_file.close()
        _LOGGER.info("System list written in %s", out_file)


def write_n2(configuration_file_path: str, n2_file_path: str = None, overwrite: bool = False):
    """
    Write the N2 diagram of the problem in file n2.html

    :param configuration_file_path:
    :param n2_file_path:
    :param overwrite:
    """

    if not n2_file_path:
        n2_file_path = pth.join(pth.dirname(configuration_file_path), "n2.html")
    n2_file_path = pth.abspath(n2_file_path)

    if not overwrite and pth.exists(n2_file_path):
        raise FastFileExistsError(
            "N2-diagram file %s not written because it already exists. "
            "Use overwrite=True to bypass." % n2_file_path,
            n2_file_path,
        )

    make_parent_dir(n2_file_path)
    problem = FASTOADProblemConfigurator(configuration_file_path).get_problem()
    problem.setup()
    problem.final_setup()

    om.n2(problem, outfile=n2_file_path, show_browser=False)
    _LOGGER.info("N2 diagram written in %s", n2_file_path)


def write_xdsm(
    configuration_file_path: str,
    xdsm_file_path: str = None,
    overwrite: bool = False,
    depth: int = 2,
    wop_server_url=None,
    api_key=None,
):
    """

    :param configuration_file_path:
    :param xdsm_file_path:
    :param overwrite:
    :param depth:
    :param wop_server_url:
    :param api_key:
    :return:
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

    problem = FASTOADProblemConfigurator(configuration_file_path).get_problem()
    problem.setup()
    problem.final_setup()

    wop = WhatsOpt(url=wop_server_url, login=False)

    try:
        ok = wop.login(api_key=api_key, echo=False)
    except requests.exceptions.ConnectionError:

        if not wop_server_url and wop.url == PROD_URL:
            used_url = wop.url
            # If connection failed while attempting to reach the wop default URL,
            # that is the internal ONERA server, try with the external server
            try:
                wop = WhatsOpt(url=DEFAULT_WOP_URL)
                ok = wop.login(api_key=api_key, echo=False)
            except requests.exceptions.ConnectionError:
                _LOGGER.warning("Failed to connect to %s and %s", used_url, DEFAULT_WOP_URL)
                return
        else:
            _LOGGER.warning("Failed to connect to %s", wop.url)
            return

    if ok:
        xdsm = wop.push_mda(
            problem, {"--xdsm": True, "--name": None, "--dry-run": False, "--depth": depth}
        )
        generate_xdsm_html(xdsm, xdsm_file_path)
    else:
        wop.logout()
        _LOGGER.warning("Could not login to %s", wop.url)


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
    :param auto_scaling: if True, automatic scaling is performed for design variables and constraints
    :return: the OpenMDAO problem after run
    """

    problem = FASTOADProblemConfigurator(configuration_file_path).get_problem(
        read_inputs=True, auto_scaling=auto_scaling
    )

    outputs_path = pth.normpath(problem.output_file_path)
    if not overwrite and pth.exists(outputs_path):
        raise FastFileExistsError(
            "Problem not run because output file %s already exists. "
            "Use overwrite=True to bypass." % outputs_path,
            outputs_path,
        )

    problem.setup()
    if mode == "run_model":
        problem.run_model()
        problem.optim_failed = False  # Actually, we don't know
    else:
        problem.optim_failed = problem.run_driver()

    problem.write_outputs()
    if problem.optim_failed:
        _LOGGER.error("Optimization failed")
    else:
        _LOGGER.info("Computation finished")

    _LOGGER.info("Problem outputs written in %s", outputs_path)

    return problem


def evaluate_problem(configuration_file_path: str, overwrite: bool = False) -> FASTOADProblem:
    """
    Runs model according to provided problem file

    :param configuration_file_path: problem definition
    :param overwrite: if True, output file will be overwritten
    :return: the OpenMDAO problem after run
    """
    return _run_problem(configuration_file_path, overwrite, "run_model")


def optimize_problem(
    configuration_file_path: str, overwrite: bool = False, auto_scaling: bool = False
) -> FASTOADProblem:
    """
    Runs driver according to provided problem file

    :param configuration_file_path: problem definition
    :param overwrite: if True, output file will be overwritten
    :param auto_scaling: if True, automatic scaling is performed for design variables and constraints
    :return: the OpenMDAO problem after run
    """
    return _run_problem(configuration_file_path, overwrite, "run_driver", auto_scaling=auto_scaling)


def optimization_viewer(configuration_file_path: str):
    """
    Displays optimization information and enables its editing

    :param configuration_file_path: problem definition
    :return: display of the OptimizationViewer
    """
    problem_configuration = FASTOADProblemConfigurator(configuration_file_path)
    viewer = OptimizationViewer()
    viewer.load(problem_configuration)

    return viewer.display()
