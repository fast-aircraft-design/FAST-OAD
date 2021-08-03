"""
API
"""
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
import warnings
import os.path as pth
import os
import sys
import tempfile
import shutil
import inspect
import importlib
import textwrap as tw
from time import time
from typing import IO, Union
from platform import system

import openmdao.api as om
from IPython import InteractiveShell
from IPython.display import HTML, clear_output, display
from tabulate import tabulate
from tempfile import TemporaryDirectory
from itertools import product
from pathlib import Path
from openmdao.core.explicitcomponent import ExplicitComponent
from openmdao.core.implicitcomponent import ImplicitComponent
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.group import Group

import fastoad.openmdao.whatsopt
from fastoad._utils.files import make_parent_dir
from fastoad._utils.resource_management.copy import copy_resource
from fastoad.cmd.exceptions import FastFileExistsError
from fastoad.gui import OptimizationViewer, VariableViewer
from fastoad.io import IVariableIOFormatter
from fastoad.io.configuration import FASTOADProblemConfigurator
from fastoad.io.variable_io import DataFile
from fastoad.io.xml import VariableLegacy1XmlFormatter
from fastoad.module_management._bundle_loader import BundleLoader
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem, RegisterPropulsion
from fastoad.openmdao.problem import FASTOADProblem
from fastoad.openmdao.variables import VariableList
from fastoad.io.configuration.configuration import AutoUnitsDefaultGroup
from fastoad.io.xml import VariableXmlStandardFormatter
from fastoad.io import VariableIO
from . import resources

DEFAULT_WOP_URL = "https://ether.onera.fr/whatsopt"
_LOGGER = logging.getLogger(__name__)
BOOLEAN_OPTIONS = [
    "use_openvsp",
    "compute_mach_interpolation",
    "compute_slipstream",
    "low_speed_aero",
]

SAMPLE_FILENAME = "fastoad.yml"
MAX_TABLE_WIDTH = 200  # For variable list text output

# Used for test purposes only
_PROBLEM_CONFIGURATOR = None


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
    :raise FastFileExistsError: if overwrite==False and out parameter is a file path and the file
                                exists
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
            return

        # Here we continue with text output
        out_file = out

        # For a terminal output, we limit width of NAME column
        variables_df["NAME"] = variables_df["NAME"].apply(lambda s: "\n".join(tw.wrap(s, 50)))

    # In any case, let's break descriptions that are too long
    variables_df["DESCRIPTION"] = variables_df["DESCRIPTION"].apply(
        lambda s: "\n".join(tw.wrap(s, 100,))
    )

    out_file.write(
        tabulate(variables_df, headers=variables_df.columns, showindex=False, tablefmt=tablefmt)
    )
    out_file.write("\n")

    if isinstance(out, str):
        out_file.close()
        _LOGGER.info("Output list written in %s", out_file)


def list_modules(
    configuration_file_path: str = None,
    out: Union[IO, str] = None,
    overwrite: bool = False,
    verbose: bool = False,
    force_text_output: bool = False,
):
    """
    Writes list of available systems.
    If configuration_file_path is given and if it defines paths where there are registered systems,
    they will be listed too.

    :param configuration_file_path:
    :param out: the output stream or a path for the output file (None means sys.stdout)
    :param overwrite: if True and out is a file path, the file will be written even if one already
                      exists
    :param verbose: if True, shows detailed information for each system
                    if False, shows only identifier and path of each system
    :param force_text_output: if True, list will be written as text, even if command is used in an
                              interactive IPython shell (Jupyter notebook). Has no effect in other
                              shells or if out parameter is not sys.stdout
   :raise FastFileExistsError: if overwrite==False and out is a file path and the file exists
    """
    if out is None:
        out = sys.stdout

    if configuration_file_path:
        conf = FASTOADProblemConfigurator(configuration_file_path)
        conf._set_configuration_modifier(_PROBLEM_CONFIGURATOR)
    # As the problem has been configured, BundleLoader now knows additional registered systems

    if verbose:
        cell_list = _get_detailed_system_list()
    else:
        cell_list = _get_simple_system_list()

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
        if (
            out == sys.stdout
            and InteractiveShell.initialized()
            and not force_text_output
            and not verbose
        ):
            display(HTML(tabulate(cell_list, tablefmt="html")))
            return

        out_file = out

    out_file.write(tabulate(cell_list, tablefmt="grid"))
    out_file.write("\n")

    if isinstance(out, str):
        out_file.close()
        _LOGGER.info("System list written in %s", out_file)


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


def write_n2(configuration_file_path: str, n2_file_path: str = "n2.html", overwrite: bool = False):
    """
    Write the N2 diagram of the problem in file n2.html

    :param configuration_file_path:
    :param n2_file_path:
    :param overwrite:
    """

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
    clear_output()
    _LOGGER.info("N2 diagram written in %s", pth.abspath(n2_file_path))


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

    conf = FASTOADProblemConfigurator(configuration_file_path)
    conf._set_configuration_modifier(_PROBLEM_CONFIGURATOR)
    problem = conf.get_problem()
    problem.setup()
    problem.final_setup()

    fastoad.openmdao.whatsopt.write_xdsm(problem, xdsm_file_path, depth, wop_server_url, dry_run)


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


def _create_tmp_directory() -> TemporaryDirectory:
    """Provide temporary directory."""

    for tmp_base_path in [None, pth.join(str(Path.home()), ".fast")]:
        if tmp_base_path is not None:
            os.makedirs(tmp_base_path, exist_ok=True)
        tmp_directory = tempfile.TemporaryDirectory(prefix="x", dir=tmp_base_path)
        break

    return tmp_directory


def file_temporary_transfer(file_path: str):
    # Put a copy of original python file into temporary directory and remove plugin registration from current file

    tmp_folder = _create_tmp_directory()
    file_name = pth.split(file_path)[-1]
    shutil.copy(file_path, pth.join(tmp_folder.name, file_name))
    file = open(file_path, "r")
    lines = file.read()
    lines = lines.split("\n")
    idx_to_remove = []
    for idx in range(len(lines)):
        if "@RegisterOpenMDAOSystem" in lines[idx]:
            idx_to_remove.append(idx)
    for idx in sorted(idx_to_remove, reverse=True):
        del lines[idx]
    file.close()
    file = open(file_path, "w")
    for line in lines:
        file.write(line + "\n")
    file.close()

    return tmp_folder


def retrieve_original_file(tmp_folder, file_path: str):
    # Retrieve the original file

    file_name = pth.split(file_path)[-1]
    shutil.copy(pth.join(tmp_folder.name, file_name), file_path)

    tmp_folder.cleanup()


def _list_all_subsystem(model, model_address, dict_subsystems):
    # noinspection PyBroadException
    try:
        # noinspection PyProtectedMember
        subsystem_list = model._proc_info.keys()
        for subsystem in subsystem_list:
            dict_subsystems = _list_all_subsystem(
                getattr(model, subsystem), model_address + "." + subsystem, dict_subsystems
            )
    except:

        def get_type(local_model):
            raw_type = local_model.msginfo.split("<")[-1]
            type_alone = raw_type.split(" ")[-1]
            model_type = type_alone[:-1]
            return model_type

        dict_subsystems[model_address] = get_type(model)

    return dict_subsystems


def _list_ivc_outputs_name(local_system: Union[ExplicitComponent, ImplicitComponent, Group]):
    # List all "root" components in the systems, meaning the components that don't have any subcomponents
    group = AutoUnitsDefaultGroup()
    group.add_subsystem("system", local_system, promotes=["*"])
    problem = FASTOADProblem(group)
    try:
        problem.setup()
    except RuntimeError:
        _LOGGER.info(
            "Some problem occurred while setting-up the problem without input file probably "
            "because shape_by_conn variables exist!"
        )
    model = problem.model
    dict_sub_system = {}
    dict_sub_system = _list_all_subsystem(model, "model", dict_sub_system)
    ivc_outputs_names = []

    # Find the outputs of all of those systems that are IndepVarComp
    for sub_system_keys in dict_sub_system.keys():
        if dict_sub_system[sub_system_keys] == "IndepVarComp":
            actual_attribute_name = sub_system_keys.replace("model.system.", "")
            address_levels = actual_attribute_name.split(".")
            component = model.system
            for next_level in address_levels:
                component = getattr(component, next_level)
            component_output = component.list_outputs()
            for outputs in component_output:
                ivc_outputs_names.append(outputs[0])

    return ivc_outputs_names


def generate_variables_description(subpackage_path: str, overwrite: bool = False):
    """
    Generates/append the variable descriptions file for a given subpackage.

    To use it simply type:
    from fastoad.cmd.api import generate_variables_description
    import my_package

    generate_variables_description(my_package.__path__[0], overwrite=True)

    :param subpackage_path: the path of the subpackage to explore
    :param overwrite: if True, the file will be written, even if it already exists
    :raise FastFileExistsError: if overwrite==False and subpackage_path already exists
    """

    if not overwrite and pth.exists(pth.join(subpackage_path, "variable_descriptions.txt")):
        # noinspection PyStringFormat
        raise FastFileExistsError(
            "Variable descriptions file is not written because it already exists. "
            "Use overwrite=True to bypass."
            % pth.join(subpackage_path, "variable_descriptions.txt"),
            pth.join(subpackage_path, "variable_descriptions.txt"),
        )

    if not pth.exists(subpackage_path):
        _LOGGER.info("Sub-package path %s not found!", subpackage_path)
    else:
        # Read file and construct dictionary of variables name index
        saved_dict = {}
        if pth.exists(pth.join(subpackage_path, "variable_descriptions.txt")):
            file = open(pth.join(subpackage_path, "variable_descriptions.txt"), "r")
            for line in file:
                if line[0] != "#" and len(line.split("||")) == 2:
                    variable_name, variable_description = line.split("||")
                    variable_name_length = len(variable_name)
                    variable_name = variable_name.replace(" ", "")
                    while variable_name_length != len(variable_name):
                        variable_name = variable_name.replace(" ", "")
                        variable_name_length = len(variable_name)
                    saved_dict[variable_name] = (variable_description, subpackage_path)
            file.close()

        # If path point to ./models directory list output variables described in the different models
        if pth.split(subpackage_path)[-1] == "models":
            for root, dirs, files in os.walk(subpackage_path, topdown=False):
                vd_file_empty_description = False
                empty_description_variables = []
                for name in files:
                    if name == "variable_descriptions.txt":
                        file = open(pth.join(root, name), "r")
                        for line in file:
                            if line[0] != "#" and len(line.split("||")) == 2:
                                variable_name, variable_description = line.split("||")
                                if variable_description.replace(" ", "") == "\n":
                                    vd_file_empty_description = True
                                    empty_description_variables.append(
                                        variable_name.replace(" ", "")
                                    )
                                variable_name_length = len(variable_name)
                                variable_name = variable_name.replace(" ", "")
                                while variable_name_length != len(variable_name):
                                    variable_name = variable_name.replace(" ", "")
                                    variable_name_length = len(variable_name)
                                if variable_name not in saved_dict.keys():
                                    saved_dict[variable_name] = (variable_description, root)
                                else:
                                    if not (
                                        pth.split(root)[-1]
                                        == pth.split(saved_dict[variable_name][1])[-1]
                                    ):
                                        warnings.warn(
                                            "file variable_descriptions.txt from subpackage "
                                            + pth.split(root)[-1]
                                            + " contains parameter "
                                            + variable_name
                                            + " already saved in "
                                            + pth.split(saved_dict[variable_name][1])[-1]
                                            + " subpackage!"
                                        )
                        file.close()
                if vd_file_empty_description:
                    warnings.warn(
                        "file variable_descriptions.txt from {} subpackage contains empty descriptions! \n".format(
                            pth.split(root)[-1]
                        )
                        + "\tFollowing variables have empty descriptions : "
                        + ", ".join(empty_description_variables)
                    )

        # Explore subpackage models and find the output variables and store them in a dictionary
        dict_to_be_saved = {}
        main_package_name = ""
        for root, dirs, files in os.walk(subpackage_path, topdown=False):
            if main_package_name == "":
                if system() != "Windows":
                    main_package_name = root.split("/")[root.split("/").index("src") + 1]
                else:
                    main_package_name = root.split("\\")[root.split("\\").index("src") + 1]
            for name in files:
                if name[-3:] == ".py":
                    spec = importlib.util.spec_from_file_location(
                        name.replace(".py", ""), pth.join(root, name)
                    )
                    module = importlib.util.module_from_spec(spec)
                    tmp_folder = None
                    # noinspection PyBroadException
                    try:
                        # if register decorator in module, temporary replace file removing decorators
                        # noinspection PyBroadException
                        try:
                            spec.loader.exec_module(module)
                        except:
                            _LOGGER.info(
                                "Trying to load {}, but it is not a module!".format(
                                    pth.join(root, name)
                                )
                            )
                        if "RegisterOpenMDAOSystem" in dir(module):
                            tmp_folder = file_temporary_transfer(pth.join(root, name))
                        spec.loader.exec_module(module)
                        class_list = [x for x in dir(module) if inspect.isclass(getattr(module, x))]
                        if "RegisterOpenMDAOSystem" in dir(module):
                            # noinspection PyUnboundLocalVariable pth.split(
                            retrieve_original_file(tmp_folder, pth.join(root, name))
                        if system() != "Windows":
                            root_lib = ".".join(root.split("/")[root.split("/").index("src") + 1 :])
                        else:
                            root_lib = ".".join(
                                root.split("\\")[root.split("\\").index("src") + 1 :]
                            )
                        root_lib += "." + name.replace(".py", "")
                        for class_name in class_list:
                            # noinspection PyBroadException
                            try:
                                my_class = getattr(importlib.import_module(root_lib), class_name)
                                options_dictionary = {}
                                if "propulsion_id" in my_class().options:
                                    available_id_list = _get_simple_system_list()
                                    idx_to_remove = []
                                    for idx in range(len(available_id_list)):
                                        available_id_list[idx] = available_id_list[idx][0]
                                        if "PROPULSION" in available_id_list[idx]:
                                            idx_to_remove.extend(list(range(idx + 1)))
                                        # Keep only propulsion registered for this package
                                        if not (main_package_name in available_id_list[idx]):
                                            idx_to_remove.append(idx)
                                    idx_to_remove = list(dict.fromkeys(idx_to_remove))
                                    for idx in sorted(idx_to_remove, reverse=True):
                                        del available_id_list[idx]
                                    options_dictionary["propulsion_id"] = available_id_list[0]
                                variables = _list_variables(my_class(**options_dictionary))
                                local_options = []
                                for option_name in BOOLEAN_OPTIONS:
                                    # noinspection PyProtectedMember
                                    if option_name in my_class().options._dict.keys():
                                        local_options.append(option_name)
                                # If no boolean options alternatives to be tested, search for input variables in models
                                # and output variables for subpackages (including ivc)
                                if len(local_options) == 0:
                                    if pth.split(subpackage_path)[-1] == "models":
                                        var_names = [var.name for var in variables if var.is_input]
                                    else:
                                        var_names = [
                                            var.name for var in variables if not var.is_input
                                        ]
                                        if (
                                            len(
                                                _list_ivc_outputs_name(
                                                    my_class(**options_dictionary)
                                                )
                                            )
                                            != 0
                                        ):
                                            var_names.append(
                                                _list_ivc_outputs_name(
                                                    my_class(**options_dictionary)
                                                )
                                            )
                                    # Remove duplicates
                                    var_names = list(dict.fromkeys(var_names))
                                    # Add to dictionary only variable name including data:, settings: or tuning:
                                    for key in var_names:
                                        if (
                                            ("data:" in key)
                                            or ("settings:" in key)
                                            or ("tuning:" in key)
                                        ):
                                            if key not in dict_to_be_saved.keys():
                                                dict_to_be_saved[key] = ""
                                # If boolean options alternatives encountered, all alternatives have to be tested to
                                # ensure complete coverage of variables. Working principle is similar to previous one.
                                else:
                                    for options_tuple in list(
                                        product([True, False], repeat=len(local_options))
                                    ):
                                        # Define local option dictionary
                                        for idx in range(len(local_options)):
                                            options_dictionary[local_options[idx]] = options_tuple[
                                                idx
                                            ]
                                        variables = _list_variables(my_class(**options_dictionary))
                                        if pth.split(subpackage_path)[-1] == "models":
                                            var_names = [
                                                var.name for var in variables if var.is_input
                                            ]
                                        else:
                                            var_names = [
                                                var.name for var in variables if not var.is_input
                                            ]
                                            if (
                                                len(
                                                    _list_ivc_outputs_name(
                                                        my_class(**options_dictionary)
                                                    )
                                                )
                                                != 0
                                            ):
                                                var_names.append(
                                                    _list_ivc_outputs_name(
                                                        my_class(**options_dictionary)
                                                    )
                                                )
                                        # Remove duplicates
                                        var_names = list(dict.fromkeys(var_names))
                                        # Add to dictionary only variable name including data:, settings: or tuning:
                                        for key in var_names:
                                            if (
                                                ("data:" in key)
                                                or ("settings:" in key)
                                                or ("tuning:" in key)
                                            ):
                                                if key not in dict_to_be_saved.keys():
                                                    dict_to_be_saved[key] = ""
                            except:
                                _LOGGER.info(
                                    "Failed to read {}.{} class parameters!".format(
                                        root_lib, class_name
                                    )
                                )
                    except:
                        if not (tmp_folder is None):
                            # noinspection PyUnboundLocalVariable
                            retrieve_original_file(tmp_folder, pth.join(root, name))

        # Complete the variable descriptions file with missing outputs
        if pth.exists(pth.join(subpackage_path, "variable_descriptions.txt")):
            file = open(pth.join(subpackage_path, "variable_descriptions.txt"), "a")
            if len(
                set(list(dict_to_be_saved.keys())).intersection(set(list(saved_dict.keys())))
            ) != len(dict_to_be_saved.keys()):
                file.write("\n")
            file.close()
        else:
            if len(dict_to_be_saved.keys()) != 0:
                file = open(pth.join(subpackage_path, "variable_descriptions.txt"), "w")
                file.write(
                    "# Documentation of variables used in {} models\n".format(
                        main_package_name.upper()
                    )
                )
                file.write("# Each line should be like:\n")
                file.write(
                    "# my:variable||The description of my:variable, as long as needed, but on one line.\n"
                )
                file.write(
                    '# The separator "||" can be surrounded with spaces (that will be ignored)\n\n'
                )
                file.close()
        if len(dict_to_be_saved.keys()) != 0:
            file = open(pth.join(subpackage_path, "variable_descriptions.txt"), "a")
            sorted_keys = sorted(dict_to_be_saved.keys(), key=lambda x: x.lower())
            added_key = False
            added_key_names = []
            for key in sorted_keys:
                if not (key in saved_dict.keys()):
                    # noinspection PyUnboundLocalVariable
                    file.write(key + " || \n")
                    added_key = True
                    added_key_names.append(key)
            file.close()
            if added_key:
                warnings.warn(
                    "file variable_descriptions.txt from {} subpackage contains empty descriptions! \n".format(
                        pth.split(subpackage_path)[-1]
                    )
                    + "\tFollowing variables have empty descriptions : "
                    + ", ".join(added_key_names)
                )


def _list_variables(component: Union[om.ExplicitComponent, om.Group]) -> list:
    """ Reads all variables from a component/problem and return as a list """
    if isinstance(component, om.Group):
        new_component = AutoUnitsDefaultGroup()
        new_component.add_subsystem("system", component, promotes=["*"])
        component = new_component
    variables = VariableList.from_system(component)

    return variables


def _write_needed_inputs(
    problem: FASTOADProblem, xml_file_path: str, source_formatter: IVariableIOFormatter = None
):
    variables = DataFile(xml_file_path)
    variables.update(
        VariableList.from_unconnected_inputs(problem, with_optional_inputs=True),
        add_variables=True,
    )
    if xml_file_path:
        ref_vars = DataFile(xml_file_path, source_formatter)
        variables.update(ref_vars)
        for var in variables:
            var.is_input = True
    variables.save()


def generate_block_analysis(
    local_system: Union[ExplicitComponent, ImplicitComponent, Group],
    var_inputs: list,
    xml_file_path: str,
    overwrite: bool = False,
):
    # Search what are the component/group outputs
    variables = _list_variables(local_system)
    inputs_names = [var.name for var in variables if var.is_input]
    outputs_names = [var.name for var in variables if not var.is_input]

    # Check the sub-systems of the local_system in question, and if there are ivc, list the outputs  of those ivc.
    # We are gonna assume that ivc are only use in a situation similar to the one for the ComputePropellerPerformance
    # group, meaning if there is an ivc, it will always start the group

    ivc_outputs_names = _list_ivc_outputs_name(local_system)

    # Check that variable inputs are in the group/component list
    if not (set(var_inputs) == set(inputs_names).intersection(set(var_inputs))):
        raise Exception("The input list contains name(s) out of component/group input list!")

    # Perform some tests on the .xml availability and completeness
    if not (os.path.exists(xml_file_path)) and not (set(var_inputs) == set(inputs_names)):
        # If no input file and some inputs are missing, generate it and return None
        group = AutoUnitsDefaultGroup()
        group.add_subsystem("system", local_system, promotes=["*"])
        problem = FASTOADProblem(group)
        problem.setup()
        _write_needed_inputs(problem, xml_file_path, VariableXmlStandardFormatter())
        raise Exception(
            "Input .xml file not found, a default file has been created with default NaN values, "
            "but no function is returned!\nConsider defining proper values before second execution!"
        )

    else:

        if os.path.exists(xml_file_path):
            reader = VariableIO(xml_file_path, VariableXmlStandardFormatter()).read(
                ignore=(var_inputs + outputs_names + ivc_outputs_names)
            )
            xml_inputs = reader.names()
        else:
            xml_inputs = []
        if not (
            set(xml_inputs + var_inputs + ivc_outputs_names).intersection(set(inputs_names))
            == set(inputs_names)
        ):
            # If some inputs are missing write an error message and add them to the problem if authorized
            missing_inputs = list(
                set(inputs_names).difference(
                    set(xml_inputs + var_inputs + ivc_outputs_names).intersection(set(inputs_names))
                )
            )
            message = "The following inputs are missing in .xml file:"
            for item in missing_inputs:
                message += " [" + item + "],"
            message = message[:-1] + ".\n"
            if overwrite:
                # noinspection PyUnboundLocalVariable
                reader.path_separator = ":"
                ivc = reader.to_ivc()
                group = AutoUnitsDefaultGroup()
                group.add_subsystem("system", local_system, promotes=["*"])
                group.add_subsystem("ivc", ivc, promotes=["*"])
                problem = FASTOADProblem(group)
                problem.input_file_path = xml_file_path
                problem.output_file_path = xml_file_path
                problem.setup()
                problem.write_outputs()
                message += (
                    "Default values have been added to {} file. "
                    "Consider modifying them for a second run!".format(xml_file_path)
                )
                raise Exception(message)
            else:
                raise Exception(message)
        else:
            # If all inputs addressed either by .xml or var_inputs or in an IVC, construct the function
            def patched_function(inputs_dict: dict) -> dict:
                """
                The patched function perform a run of an openmdao component or group applying FASTOAD formalism.

                @param inputs_dict: dictionary of input (values, units) saved with their key name,
                as an example: inputs_dict = {'in1': (3.0, "m")}.
                @return: dictionary of the component/group outputs saving names as keys and (value, units) as tuple.
                """

                # Read .xml file and construct Independent Variable Component excluding outputs
                if os.path.exists(xml_file_path):
                    reader.path_separator = ":"
                    ivc_local = reader.to_ivc()
                else:
                    ivc_local = IndepVarComp()
                for name, value in inputs_dict.items():
                    ivc_local.add_output(name, value[0], units=value[1])
                group_local = AutoUnitsDefaultGroup()
                group_local.add_subsystem("system", local_system, promotes=["*"])
                group_local.add_subsystem("ivc", ivc_local, promotes=["*"])
                problem_local = FASTOADProblem(group_local)
                problem_local.setup()
                problem_local.run_model()
                if overwrite:
                    problem_local.output_file_path = xml_file_path
                    problem_local.write_outputs()
                # Get output names from component/group and construct dictionary
                outputs_units = [var.units for var in variables if not var.is_input]
                outputs_dict = {}
                for idx in range(len(outputs_names)):
                    value = problem_local.get_val(outputs_names[idx], outputs_units[idx])
                    outputs_dict[outputs_names[idx]] = (value, outputs_units[idx])
                return outputs_dict

            return patched_function
