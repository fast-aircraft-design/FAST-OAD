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

import contextlib
from math import isnan
from pathlib import Path
from typing import ClassVar

import ipywidgets as widgets
import numpy as np
import pandas as pd
from IPython.display import clear_output, display
from ipydatagrid import DataGrid, TextRenderer

from fastoad.io import DataFile
from fastoad.io.configuration.configuration import (
    KEY_CONSTRAINTS,
    KEY_DESIGN_VARIABLES,
    KEY_OBJECTIVE,
    FASTOADProblemConfigurator,
)
from fastoad.openmdao.variables import Variable, VariableList

from .exceptions import FastMissingFileError

pd.set_option("display.max_rows", None)

# Columns that are read-only in the grid (cannot be edited by the user)
_READ_ONLY_COLUMNS = {"Name", "Unit", "Description", "Value"}
# Columns that can be edited by the user
_EDITABLE_COLUMNS = {"Initial Value", "Lower", "Upper"}


class OptimizationViewer:
    """
    A class for interacting with FAST-OAD Problem optimization information.
    """

    # When getting a dataframe from a VariableList, the dictionary keys tell what columns
    #  are kept and values tell what name will be displayed.
    _DEFAULT_COLUMN_RENAMING: ClassVar[dict] = {
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

        # The grid for design variables
        self._design_var_grid = None
        self._design_var_indices: list = []

        # The grid for constraints
        self._constraint_grid = None
        self._constraint_indices: list = []

        # The grid for objectives
        self._objective_grid = None
        self._objective_indices: list = []

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
            raise FastMissingFileError(
                "Please generate input file before using the optimization viewer"
            )

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
    def _update_optim_variable(variable: Variable, optim_definition: dict):
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

    def load_variables(
        self, variables: VariableList, attribute_to_column: dict[str, str] | None = None
    ):
        """
        Loads provided variable list and replace current data set.

        :param variables: the variables to load
        :param attribute_to_column: dictionary keys tell what variable attributes are
               kept and the values tell what name will be displayed. If not provided,
               default translation will apply.
        """

        if not attribute_to_column:
            attribute_to_column = OptimizationViewer._DEFAULT_COLUMN_RENAMING

        self.dataframe = (
            variables.to_dataframe()
            .rename(columns=attribute_to_column)[attribute_to_column.values()]
            .reset_index(drop=True)
        )

    def get_variables(self, column_to_attribute: dict[str, str] | None = None) -> VariableList:
        """

        :param column_to_attribute: dictionary keys tell what columns are kept and the values
                                    tell whatvariable attribute it corresponds to. If not
                                    provided, default translation will apply.
        :return: a variable list from current data set
        """
        if not column_to_attribute:
            column_to_attribute = {
                value: key for key, value in OptimizationViewer._DEFAULT_COLUMN_RENAMING.items()
            }

        return VariableList.from_dataframe(
            self.dataframe[column_to_attribute.keys()].rename(columns=column_to_attribute)
        )

    def _df_to_grid(self, df: pd.DataFrame) -> DataGrid:
        """
        Transforms a pandas DataFrame into an ipydatagrid DataGrid.

        Columns in ``_READ_ONLY_COLUMNS`` are rendered with a grey background to
        signal they are not editable.  The grid itself is editable so that the
        user can modify the bound / initial-value columns.

        If ``self._MISSING_OUTPUT_FILE`` is True, the *Value* column cells are
        replaced with ``"-"`` to indicate that no output is available.

        :param df: the pandas DataFrame to be converted
        :return: the DataGrid widget
        """
        if df.empty:
            return DataGrid(pd.DataFrame(), editable=True, layout=widgets.Layout(height="100px"))

        display_df = df.copy().reset_index(drop=True)

        if self._MISSING_OUTPUT_FILE and "Value" in display_df.columns:
            display_df["Value"] = "-"

        # Build per-column renderers: grey background for read-only columns
        renderers = {
            col: TextRenderer(background_color="#f0f0f0")
            for col in display_df.columns
            if col in _READ_ONLY_COLUMNS
        }

        # Colour active/violated bounds (yellow = active within threshold, red = violated)
        # TODO: replace with ipydatagrid VegaExpr conditional formatting for live updates
        style = self._cell_styling(df)
        for (r, c), cell_style in style.items():
            if c in display_df.columns and cell_style.get("backgroundColor"):
                color = cell_style["backgroundColor"]
                existing = renderers.get(c, TextRenderer())
                existing.background_color = color
                renderers[c] = existing

        return DataGrid(
            display_df,
            editable=True,
            renderers=renderers,
            layout=widgets.Layout(height="200px"),
            column_widths={
                "Name": 300,
                "Value": 80,
                "Unit": 60,
                "Description": 300,
                "Initial Value": 80,
                "Lower": 80,
                "Upper": 80,
            },
        )

    def _make_update_callback(self, grid_indices: list):
        """
        Returns an ``on_cell_change`` callback that updates ``self.dataframe``
        for the rows identified by *grid_indices*.

        Only columns in ``_EDITABLE_COLUMNS`` trigger an update; changes to
        read-only columns are silently ignored.

        :param grid_indices: list mapping grid row index → original dataframe index
        """

        def callback(cell: dict):
            col = cell["column"]
            if col not in _EDITABLE_COLUMNS:
                return
            grid_row = cell["row"]
            if grid_row >= len(grid_indices):
                return
            original_idx = grid_indices[grid_row]
            value = cell["value"]
            with contextlib.suppress(ValueError, TypeError):
                value = float(value)
            self.dataframe.loc[original_idx, col] = value

        return callback

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
        Rebuilds the three DataGrids (design variables, constraints, objectives)
        from the current state of ``self.dataframe``.
        """
        # Design variables
        design_var_df = self.dataframe[self.dataframe["Type"] == "design_var"].drop(
            columns=["Type"]
        )
        self._design_var_indices = design_var_df.index.tolist()
        self._design_var_grid = self._df_to_grid(design_var_df)
        self._design_var_grid.on_cell_change(self._make_update_callback(self._design_var_indices))

        # Constraints
        constraint_df = self.dataframe[self.dataframe["Type"] == "constraint"].drop(
            columns=["Type", "Initial Value"]
        )
        self._constraint_indices = constraint_df.index.tolist()
        self._constraint_grid = self._df_to_grid(constraint_df)
        self._constraint_grid.on_cell_change(self._make_update_callback(self._constraint_indices))

        # Objectives
        objective_df = self.dataframe[self.dataframe["Type"] == "objective"].drop(
            columns=["Type", "Initial Value", "Lower", "Upper"]
        )
        self._objective_indices = objective_df.index.tolist()
        self._objective_grid = self._df_to_grid(objective_df)
        self._objective_grid.on_cell_change(self._make_update_callback(self._objective_indices))

    # change has to be there for observe() to work
    def _render_ui(self, change=None) -> display:
        """
        Renders the dropdown menus for the variable selector and the corresponding
        DataGrids containing the variable infos.

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
        return widgets.VBox([widgets.Label(value="Design Variables"), self._design_var_grid])

    def _constraint_ui(self):
        return widgets.VBox([widgets.Label(value="Constraints"), self._constraint_grid])

    def _objective_ui(self):
        return widgets.VBox([widgets.Label(value="Objectives"), self._objective_grid])

    @staticmethod
    def _cell_styling(df) -> dict:
        """
        Returns bound activities in the form of a cell style dictionary.

        :return: dict mapping ``(row_index, column_name)`` → style dict
        """

        def highlight_active_bounds(df, threshold=1e-6):
            rows = df.index.tolist()
            columns = df.columns.tolist()
            style = {}
            for r in rows:
                s = df.loc[r]
                is_active = pd.Series(data=False, index=s.index)
                is_violated = pd.Series(data=False, index=s.index)
                if ("Lower" in s) and (s.loc["Lower"] is not None):
                    # Constraints might only have a upper bound
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

                if ("Upper" in s) and (s.loc["Upper"] is not None):
                    # Constraints might only have a lower bound
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

        return highlight_active_bounds(df, threshold=0.1)  # Style
