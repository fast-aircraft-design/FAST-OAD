"""
Defines the variable viewer for postprocessing
"""
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

from math import isnan
from pathlib import Path
from typing import Dict

import ipysheet as sh
import ipywidgets as widgets
import numpy as np
import pandas as pd
from IPython.display import clear_output, display

from fastoad.io import DataFile
from fastoad.io.configuration.configuration import (
    FASTOADProblemConfigurator,
    KEY_CONSTRAINTS,
    KEY_DESIGN_VARIABLES,
    KEY_OBJECTIVE,
)
from fastoad.openmdao.variables import Variable, VariableList
from .exceptions import FastMissingFile

pd.set_option("display.max_rows", None)


class OptimizationViewer:
    """
    A class for interacting with FAST-OAD Problem optimization information.
    """

    # When getting a dataframe from a VariableList, the dictionary keys tell what columns
    #  are kept and values tell what name will be displayed.
    _DEFAULT_COLUMN_RENAMING = {
        "type": "Type",
        "name": "Name",
        "initial_value": "Initial Value",
        "lower": "Lower",
        "val": "Value",
        "upper": "Upper",
        "units": "Unit",
        "desc": "Description",
    }

    def __init__(self):

        #: Instance of the FAST-OAD problem configuration
        self.problem_configuration: FASTOADProblemConfigurator = None

        #: The dataframe which is the mirror of self.file
        self.dataframe = pd.DataFrame()

        # The sheet which is the mirror of the design var sheet
        self._design_var_sheet = None

        # The sheet which is the mirror of the constraint sheet
        self._constraint_sheet = None

        # The sheet which is the mirror of the objective sheet
        self._objective_sheet = None

        # The ui containing save and load buttons
        self._save_load_buttons = None

        # True if in the absence of an output file
        self._MISSING_OUTPUT_FILE = None

    def load(self, problem_configuration: FASTOADProblemConfigurator):
        """
        Loads the FAST-OAD problem and stores its data.

        :param problem_configuration: the FASTOADProblem instance.
        """

        self.problem_configuration = problem_configuration

        if Path(self.problem_configuration.input_file_path).is_file():
            input_variables = DataFile(self.problem_configuration.input_file_path)
        else:
            # TODO: generate the input file by default ?
            raise FastMissingFile("Please generate input file before using the optimization viewer")

        if Path(self.problem_configuration.output_file_path).is_file():
            self._MISSING_OUTPUT_FILE = False
            output_variables = DataFile(self.problem_configuration.output_file_path)
        else:
            self._MISSING_OUTPUT_FILE = True
            problem = self.problem_configuration.get_problem()
            problem.setup()
            output_variables = VariableList.from_problem(problem)

        optimization_variables = VariableList()
        opt_def = problem_configuration.get_optimization_definition()
        # Design Variables
        if KEY_DESIGN_VARIABLES in opt_def:
            for name, design_var in opt_def[KEY_DESIGN_VARIABLES].items():
                metadata = {
                    "type": "design_var",
                    "initial_value": input_variables[name].value,
                    "lower": design_var.get("lower"),
                    "value": output_variables[name].value,
                    "upper": design_var.get("upper"),
                    "units": input_variables[name].units,
                    "desc": input_variables[name].description,
                }
                optimization_variables[name] = metadata

        # Constraints
        if KEY_CONSTRAINTS in opt_def:
            for name, constr in opt_def[KEY_CONSTRAINTS].items():
                metadata = {
                    "type": "constraint",
                    "initial_value": None,
                    "lower": constr.get("lower"),
                    "value": output_variables[name].value,
                    "upper": constr.get("upper"),
                    "units": output_variables[name].units,
                    "desc": output_variables[name].description,
                }
                optimization_variables[name] = metadata

        # Objectives
        if KEY_OBJECTIVE in opt_def:
            for name in opt_def[KEY_OBJECTIVE]:
                metadata = {
                    "type": "objective",
                    "initial_value": None,
                    "lower": None,
                    "value": output_variables[name].value,
                    "upper": None,
                    "units": output_variables[name].units,
                    "desc": output_variables[name].description,
                }
                optimization_variables[name] = metadata

        self.load_variables(optimization_variables)

    def save(self):
        """
        Save the optimization to the files.
        Possible files modified are:
            - the .yml configuration file
            - the input file (initial values)
            - the output file (values)
        """
        conf = self.problem_configuration
        input_variables = DataFile(self.problem_configuration.input_file_path, None)
        opt_def = conf.get_optimization_definition()

        variables = self.get_variables()
        for variable in variables:
            name = variable.name
            if name in input_variables.names():
                input_variables[name].value = variable.metadata["initial_value"]
            self._update_optim_variable(variable, opt_def)

        # Saving modifications
        # Initial values
        input_variables.save()

        # Optimization definition
        conf.set_optimization_definition(opt_def)
        conf.save()

    @staticmethod
    def _update_optim_variable(variable: Variable, optim_definition: Dict):
        """
        Updates optim_definition with metadata of provided variable.

        :param variable:
        :param optim_definition:
        """
        name = variable.name
        meta = variable.metadata

        if meta["type"] == "design_var":
            # TODO: later it will be possible to add/remove design variables in the ui
            section_name = KEY_DESIGN_VARIABLES
        elif meta["type"] == "constraint":
            # TODO: later it will be possible to add/remove constraints in the ui
            section_name = KEY_CONSTRAINTS
        else:
            return

        if section_name not in optim_definition:
            optim_definition[section_name] = {}
        if name not in optim_definition[section_name]:
            optim_definition[section_name][name] = {}
        for bound in ["lower", "upper"]:
            if meta[bound] is not None and not isnan(meta[bound]):
                optim_definition[section_name][name].update({bound: meta[bound]})
            else:
                optim_definition[section_name][name].pop(bound, None)

    def display(self):
        """
        Displays the datasheet.
        load() must be ran before.

        :return: display of the user interface:
        """
        self._create_save_load_buttons()
        return self._render_ui()

    def load_variables(self, variables: VariableList, attribute_to_column: Dict[str, str] = None):
        """
        Loads provided variable list and replace current data set.

        :param variables: the variables to load
        :param attribute_to_column: dictionary keys tell what variable attributes are
               kept and the values tell what name will be displayed. If not provided,
               default translation will apply.
        """

        if not attribute_to_column:
            attribute_to_column = self._DEFAULT_COLUMN_RENAMING

        self.dataframe = (
            variables.to_dataframe()
            .rename(columns=attribute_to_column)[attribute_to_column.values()]
            .reset_index(drop=True)
        )

    def get_variables(self, column_to_attribute: Dict[str, str] = None) -> VariableList:
        """

        :param column_to_attribute: dictionary keys tell what columns are kept and the values
                                    tell whatvariable attribute it corresponds to. If not
                                    provided, default translation will apply.
        :return: a variable list from current data set
        """
        if not column_to_attribute:
            column_to_attribute = {
                value: key for key, value in self._DEFAULT_COLUMN_RENAMING.items()
            }

        return VariableList.from_dataframe(
            self.dataframe[column_to_attribute.keys()].rename(columns=column_to_attribute)
        )

    # pylint: disable=invalid-name # df is a common naming for dataframes
    def _df_to_sheet(self, df: pd.DataFrame) -> sh.Sheet:
        """
        Transforms a pandas DataFrame into a ipysheet Sheet.
        The cells are set to read only except for the values.

        :param df: the pandas DataFrame to be converted
        :return: the equivalent ipysheet Sheet
        """
        if not df.empty:
            # Adapted from_dataframe() method of ipysheet
            columns = df.columns.tolist()
            rows = df.index.tolist()
            cells = []

            read_only_cells = ["Name", "Unit", "Description", "Value"]

            style = self._cell_styling(df)
            row_idx = 0
            for r in rows:
                col_idx = 0
                for c in columns:
                    value = df.loc[r, c]
                    if c in read_only_cells:
                        read_only = True
                        numeric_format = None
                    else:
                        read_only = False
                        # TODO: make the number of decimals depend on the module ?
                        # or chosen in the ui by the user
                        numeric_format = "0.000"

                    # If no output file is provided make it clearer for the user
                    if c == "Value" and self._MISSING_OUTPUT_FILE:
                        value = "-"

                    cells.append(
                        sh.Cell(
                            value=value,
                            row_start=row_idx,
                            row_end=row_idx,
                            column_start=col_idx,
                            column_end=col_idx,
                            numeric_format=numeric_format,
                            read_only=read_only,
                            style=style[(r, c)],
                        )
                    )
                    col_idx += 1
                row_idx += 1
            sheet = sh.Sheet(
                rows=len(rows),
                columns=len(columns),
                cells=cells,
                row_headers=[str(header) for header in rows],
                column_headers=[str(header) for header in columns],
            )

        else:
            sheet = sh.sheet(rows=0, columns=0)

        return sheet

    @staticmethod
    def _sheet_to_df(sheet: sh.Sheet) -> pd.DataFrame:
        """
        Transforms a ipysheet Sheet into a pandas DataFrame.

        :param sheet: the ipysheet Sheet to be converted
        :return: the equivalent pandas DataFrame
        """
        df = sh.to_dataframe(sheet)
        return df

    # pylint: disable=unused-argument  # args has to be there for observe() to work
    def _update_df(self, change=None):
        """
        Updates the stored DataFrame with respect to the actual values of the Sheet.
        Then updates the file with respect to the stored DataFrame.
        """
        frames = [
            self._sheet_to_df(self._design_var_sheet),
            self._sheet_to_df(self._constraint_sheet),
            self._sheet_to_df(self._objective_sheet),
        ]

        df = pd.concat(frames, sort=True)
        columns = {}
        columns.update(self._DEFAULT_COLUMN_RENAMING)
        columns.pop("type")

        column_to_attribute = {value: key for key, value in columns.items()}

        variables = VariableList.from_dataframe(
            df[column_to_attribute.keys()].rename(columns=column_to_attribute)
        )

        attribute_to_column = columns
        df = (
            variables.to_dataframe()
            .rename(columns=attribute_to_column)[attribute_to_column.values()]
            .reset_index(drop=True)
        )
        rows = df.index.tolist()
        columns = df.columns.tolist()

        for r in rows:
            for c in columns:
                self.dataframe.loc[int(r), c] = df.loc[r, c]

    def _create_save_load_buttons(self):
        """
        The save button saves the present state of the dataframe to the xml.
        The load button loads the xml and replaces actual the dataframe.
        """

        save_button = widgets.Button(
            description="Save",
            disabled=False,
            button_style="",  # 'success', 'info', 'warning', 'danger' or ''
            tooltip="Save to the file",
            icon="save",
        )

        def on_save_button_clicked(b):
            self.save()

        save_button.on_click(on_save_button_clicked)

        load_button = widgets.Button(
            description="Load",
            disabled=False,
            button_style="",  # 'success', 'info', 'warning', 'danger' or ''
            tooltip="Load the file",
            icon="upload",
        )

        def on_load_button_clicked(b):
            self.load(self.problem_configuration)
            self._render_ui()

        load_button.on_click(on_load_button_clicked)

        items_box = widgets.HBox([load_button, save_button])

        self._save_load_buttons = items_box

    def _update_sheet(self):
        """
        Updates the sheet after filtering the dataframe with respect to
        the actual values of the variable dropdown menus.
        """
        design_var_df = self.dataframe[self.dataframe["Type"] == "design_var"]
        design_var_df = design_var_df.drop(columns=["Type"])
        self._design_var_sheet = self._df_to_sheet(design_var_df)
        constraint_df = self.dataframe[self.dataframe["Type"] == "constraint"]
        constraint_df = constraint_df.drop(columns=["Type", "Initial Value"])
        self._constraint_sheet = self._df_to_sheet(constraint_df)
        objective_df = self.dataframe[self.dataframe["Type"] == "objective"]
        objective_df = objective_df.drop(columns=["Type", "Initial Value", "Lower", "Upper"])
        self._objective_sheet = self._df_to_sheet(objective_df)

        for cell in self._design_var_sheet.cells:
            cell.observe(self._update_df, "value")
            cell.observe(self._update_style, "value")

        for cell in self._constraint_sheet.cells:
            cell.observe(self._update_df, "value")
            cell.observe(self._update_style, "value")

        for cell in self._objective_sheet.cells:
            cell.observe(self._update_df, "value")
            cell.observe(self._update_style, "value")

    # pylint: disable=unused-argument  # args has to be there for observe() to work
    def _render_ui(self, change=None) -> display:
        """
        Renders the dropdown menus for the variable selector and the corresponding
        ipysheet Sheet containing the variable infos.

        :return: the display object
        """
        clear_output(wait=True)
        self._update_sheet()
        ui = widgets.VBox(
            [
                self._save_load_buttons,
                self._design_var_ui(),
                self._constraint_ui(),
                self._objective_ui(),
            ]
        )
        return display(ui)

    def _design_var_ui(self):
        return widgets.VBox([widgets.Label(value="Design Variables"), self._design_var_sheet])

    def _constraint_ui(self):
        return widgets.VBox([widgets.Label(value="Constraints"), self._constraint_sheet])

    def _objective_ui(self):
        return widgets.VBox([widgets.Label(value="Objectives"), self._objective_sheet])

    @staticmethod
    def _cell_styling(df) -> Dict:
        """
        Returns bound activities in the form of cell style dictionary.

        :return: dict containing the style
        """

        def highlight_active_bounds(df, threshold=1e-6):
            rows = df.index.tolist()
            columns = df.columns.tolist()
            style = {}
            for r in rows:
                s = df.loc[r]
                is_active = pd.Series(data=False, index=s.index)
                is_violated = pd.Series(data=False, index=s.index)
                if "Lower" in s:
                    # Constraints might only have a upper bound
                    if s.loc["Lower"] is not None:
                        if np.all(s.loc["Lower"] + threshold >= s.loc["Value"]) & np.all(
                            s.loc["Value"] >= s.loc["Lower"] - threshold
                        ):
                            is_active["Lower"] = True
                            is_active["Value"] = True
                        elif np.all(s.loc["Value"] < s.loc["Lower"] - threshold):
                            is_violated["Lower"] = True
                            is_violated["Value"] = True
                        else:
                            pass

                if "Upper" in s:
                    # Constraints might only have a lower bound
                    if s.loc["Upper"] is not None:
                        if np.all(s.loc["Upper"] + threshold >= s.loc["Value"]) & np.all(
                            s.loc["Value"] >= s.loc["Upper"] - threshold
                        ):
                            is_active["Upper"] = True
                            is_active["Value"] = True
                        elif np.all(s.loc["Value"] > s.loc["Upper"] + threshold):
                            is_violated["Upper"] = True
                            is_violated["Value"] = True
                        else:
                            pass

                yellow = ["yellow" if v else None for v in is_active]
                red = ["red" if v else None for v in is_violated]
                column_styles = [
                    {"backgroundColor": y_style or r_style} for y_style, r_style in zip(yellow, red)
                ]

                for column, column_style in zip(columns, column_styles):
                    style[(r, column)] = column_style

            return style

        style = highlight_active_bounds(df, threshold=0.1)
        # style.update(another_styling_method())

        return style

    def _update_style(self, change=None):
        """
        Updates the style of the sheet cells with respect to bound activities
        of the actual self.dataframe.
        """
        # Design variables
        design_var_df = self.dataframe[self.dataframe["Type"] == "design_var"]
        design_var_df = design_var_df.drop(columns=["Type"])
        design_var_df = design_var_df.reset_index(drop=True)
        style = self._cell_styling(design_var_df)

        for cell in self._design_var_sheet.cells:
            i, j = cell.row_start, cell.column_start
            r, c = (design_var_df.index.to_list()[i], design_var_df.columns.to_list()[j])
            cell.style = style[(r, c)]

        #  Constraints
        constraint_df = self.dataframe[self.dataframe["Type"] == "constraint"]
        constraint_df = constraint_df.drop(columns=["Type", "Initial Value"])
        constraint_df = constraint_df.reset_index(drop=True)
        style = self._cell_styling(constraint_df)

        for cell in self._constraint_sheet.cells:
            i, j = cell.row_start, cell.column_start
            r, c = (constraint_df.index.to_list()[i], constraint_df.columns.to_list()[j])
            cell.style = style[(r, c)]

        # Objectives
        objective_df = self.dataframe[self.dataframe["Type"] == "objective"]
        objective_df = objective_df.drop(columns=["Type", "Initial Value", "Lower", "Upper"])
        objective_df = objective_df.reset_index(drop=True)
        style = self._cell_styling(objective_df)

        for cell in self._objective_sheet.cells:
            i, j = cell.row_start, cell.column_start
            r, c = (objective_df.index.to_list()[i], objective_df.columns.to_list()[j])
            cell.style = style[(r, c)]
