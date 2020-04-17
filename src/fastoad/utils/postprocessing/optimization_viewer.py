"""
Defines the variable viewer for postprocessing
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

from typing import List, Set, Dict

import ipysheet as sh
import ipywidgets as widgets
import pandas as pd
from IPython.display import display, clear_output
from fastoad.io.configuration import FASTOADProblem
from fastoad.io import VariableIO, IVariableIOFormatter
from fastoad.openmdao.variables import VariableList

pd.set_option("display.max_rows", None)


class OptimizationViewer:
    """
    A class for interacting with FAST-OAD Problem optimization information.
    """

    # When getting a dataframe from a VariableList, the dictionary keys tell what columns are kept and
    # the values tell what name will be displayed.
    _DEFAULT_COLUMN_RENAMING = {
        "type": "Type",
        "name": "Name",
        "initial_value": "Initial Value",
        "lower": "Lower",
        "value": "Value",
        "upper": "Upper",
        "units": "Unit",
        "desc": "Description",
    }

    def __init__(self):

        # Instance of the FAST-OAD problem
        self.problem = None

        # The dataframe which is the mirror of the self.file
        self.dataframe = pd.DataFrame()

        # The sheet which is the mirror of the design var sheet
        self._design_var_sheet = None

        # The sheet which is the mirror of the constraint sheet
        self._constraint_sheet = None

        # The sheet which is the mirror of the objective sheet
        self._objective_sheet = None

        # The ui containing save and load buttons
        self._save_load_buttons = None

    def load(self, problem: FASTOADProblem, file_formatter: IVariableIOFormatter = None):
        """
        Loads the FAST-OAD problem and stores its data.

        :param problem: the FASTOADProblem instance.
        :param file_formatter: the formatter that defines file format. If not provided, default format will be assumed.
        """

        self.problem = problem
        input_variables = VariableIO(self.problem.input_file_path, file_formatter).read()
        output_variables = VariableIO(self.problem.output_file_path, file_formatter).read()
        optimization_variables = VariableList()
        opt_def = problem._optimization_definition
        # Design Variables
        if "design_var" in opt_def:
            for design_var in opt_def["design_var"]:
                name = design_var["name"]
                initial_value = input_variables[name].value
                # TODO: check that lower is provided
                lower = design_var["lower"]
                value = output_variables[name].value
                # TODO: check that upper is provided
                upper = design_var["upper"]
                units = output_variables[name].units
                desc = output_variables[name].description
                metadata = {
                    "type": "design_var",
                    "initial_value": initial_value,
                    "lower": lower,
                    "value": value,
                    "upper": upper,
                    "units": units,
                    "desc": desc,
                }
                optimization_variables[name] = metadata

        # Constraints
        if "constraint" in opt_def:
            for constr in opt_def["constraint"]:
                name = constr["name"]
                # TODO: check that lower is provided
                lower = constr["lower"]
                value = output_variables[name].value
                # TODO: check that upper is provided
                upper = constr["upper"]
                units = output_variables[name].units
                desc = output_variables[name].description
                metadata = {
                    "type": "constraint",
                    "initial_value": None,
                    "lower": lower,
                    "value": value,
                    "upper": upper,
                    "units": units,
                    "desc": desc,
                }
                optimization_variables[name] = metadata

        # Objectives
        if "objective" in opt_def:
            for obj in opt_def["objective"]:
                name = obj["name"]
                value = output_variables[name].value
                units = output_variables[name].units
                desc = output_variables[name].description
                metadata = {
                    "type": "objective",
                    "initial_value": None,
                    "lower": None,
                    "value": value,
                    "upper": None,
                    "units": units,
                    "desc": desc,
                }
                optimization_variables[name] = metadata

        self.load_variables(optimization_variables)

    def save(self, file_path: str = None, file_formatter: IVariableIOFormatter = None):
        """
        Save the dataframe to the file.

        :param file_path: the path of file to save. If not given, the initially read file will be overwritten.
        :param file_formatter: the formatter that defines file format. If not provided, default format will be assumed.
       """
        if file_path is None:
            file_path = self.file

        variables = self.get_variables()

        VariableIO(file_path, file_formatter).write(variables)

    def display(self):
        """
        Displays the datasheet
        :return display of the user interface:
        """
        self._create_save_load_buttons()
        return self._render_sheet()

    def load_variables(self, variables: VariableList, attribute_to_column: Dict[str, str] = None):
        """
        Loads provided variable list and replace current data set.

        :param variables: the variables to load
        :param attribute_to_column: dictionary keys tell what variable attributes are kept and the values tell what
                                     name will be displayed. If not provided, default translation will apply.
        """

        if not attribute_to_column:
            attribute_to_column = self._DEFAULT_COLUMN_RENAMING

        self.dataframe = (
            variables.to_dataframe()
            .rename(columns=attribute_to_column)[attribute_to_column.values()]
            .reset_index(drop=True)
        )
        # Apply coloring
        self.dataframe = self._bound_activity_coloring(self.dataframe)

    def get_variables(self, column_to_attribute: Dict[str, str] = None) -> VariableList:
        """

        :param column_to_attribute: dictionary keys tell what columns are kept and the values tell what
                                     variable attribute it corresponds to. If not provided, default translation
                                     will apply.
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
    @staticmethod
    def _df_to_sheet(df: pd.DataFrame) -> sh.Sheet:
        """
        Transforms a pandas DataFrame into a ipysheet Sheet.
        The cells are set to read only except for the values.

        :param df: the pandas DataFrame to be converted
        :return the equivalent ipysheet Sheet
        """
        if not df.empty:
            sheet = sh.from_dataframe(df)
            name_column = df.columns.get_loc("Name")
            units_column = df.columns.get_loc("Unit")
            desc_column = df.columns.get_loc("Description")

            for cell in sheet.cells:
                if units_column in (cell.column_start, cell.column_end):
                    cell.read_only = True
                elif desc_column in (cell.column_start, cell.column_end):
                    cell.read_only = True
                elif name_column in (cell.column_start, cell.column_end):
                    cell.read_only = True
                else:
                    cell.type = "numeric"
                    # TODO: make the number of decimals depend on the module ?
                    # or chosen in the ui by the user
                    cell.numeric_format = "0.000"

        else:
            sheet = sh.sheet()
        return sheet

    @staticmethod
    def _sheet_to_df(sheet: sh.Sheet) -> pd.DataFrame:
        """
        Transforms a ipysheet Sheet into a pandas DataFrame.

        :param sheet: the ipysheet Sheet to be converted
        :return the equivalent pandas DataFrame
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
        df = pd.concat(frames)
        for i in df.index:
            self.dataframe.loc[int(i), :] = df.loc[i, :].values

        # Apply coloring
        # self.dataframe = self._bound_activity_coloring(self.dataframe)

    def _render_sheet(self) -> display:
        """
        Renders an interactive pysheet with dropdown menus of the stored dataframe.

        :return display of the user interface
        """
        return self._render_ui()

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
            self.load(self.file)
            self._render_sheet()

        load_button.on_click(on_load_button_clicked)

        items_box = widgets.HBox([save_button, load_button])

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

        for cell in self._constraint_sheet.cells:
            cell.observe(self._update_df, "value")

        for cell in self._objective_sheet.cells:
            cell.observe(self._update_df, "value")

    # pylint: disable=unused-argument  # args has to be there for observe() to work
    def _render_ui(self, change=None) -> display:
        """
        Renders the dropdown menus for the variable selector and the corresponding
        ipysheet Sheet containing the variable infos.

        :return the display object
        """
        clear_output(wait=True)
        self._update_sheet()
        # self._sheet.layout.height = "400px"
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
    def _bound_activity_coloring(df):
        def highlight_active_bounds(s, threshold):
            is_active = pd.Series(data=False, index=s.index)
            is_violated = pd.Series(data=False, index=s.index)

            # Constraints might only have a upper bound
            if s.loc["Lower"] is not None:
                if s.loc["Lower"] + threshold >= s.loc["Value"] >= s.loc["Lower"] - threshold:
                    is_active["Lower"] = True
                    is_active["Value"] = True
                elif s.loc["Value"] < s.loc["Lower"] - threshold:
                    is_violated["Lower"] = True
                    is_violated["Value"] = True
                else:
                    pass

            # Constraints might only have a lower bound
            if s.loc["Upper"] is not None:
                if s.loc["Upper"] + threshold >= s.loc["Value"] >= s.loc["Upper"] - threshold:
                    is_active["Upper"] = True
                    is_active["Value"] = True
                elif s.loc["Value"] > s.loc["Upper"] + threshold:
                    is_violated["Upper"] = True
                    is_violated["Value"] = True
                else:
                    pass
            yellow = ["background-color: yellow" if v else "" for v in is_active]
            red = ["background-color: red" if v else "" for v in is_violated]
            style = [yellow[i] or red[i] for i in range(len(yellow))]
            return style

        df = df.style.apply(highlight_active_bounds, threshold=10.0, axis=1)
        return df
