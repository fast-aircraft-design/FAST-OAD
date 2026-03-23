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

import ast
from os import PathLike
from typing import ClassVar

import ipywidgets as widgets
import numpy as np
import pandas as pd
from IPython.display import display
from ipydatagrid import DataGrid

from fastoad.io import IVariableIOFormatter, VariableIO
from fastoad.openmdao.variables import VariableList

pd.set_option("display.max_rows", None)
INPUT = "IN"
OUTPUT = "OUT"
NA = "N/A"
TAG_ALL = "--ALL--"


class VariableViewer:
    """
    A class for interacting with FAST-OAD files.
    The file data is stored in a pandas DataFrame. The class built so that a modification
    of the DataFrame is instantly replicated on the file file.
    The interaction is achieved using a user interface built with widgets from ipywidgets and
    a DataGrid from ipydatagrid.

    A classical usage of this class will be::

        df = VariableViewer()  # instantiation of dataframe
        file = AbstractOMFileIO('problem_outputs.file') #  instantiation of file io
        df.load(file)  # load the file
        df.display()  # renders a ui for reading/modifying the file
    """

    # When getting a dataframe from a VariableList, the dictionary keys tell
    # what columns are kept and the values tell what name will be displayed.
    _DEFAULT_COLUMN_RENAMING: ClassVar[dict] = {
        "name": "Name",
        "val": "Value",
        "units": "Unit",
        "desc": "Description",
        "is_input": "is_input",
    }

    def __init__(self):
        #: The path of the data file that will be viewed/edited
        self.file = None

        #: The dataframe which is the mirror of self.file
        self.dataframe = pd.DataFrame()

        # The grid which is the mirror of the filtered dataframe
        self._grid = None

        # Original dataframe indices for the currently displayed (filtered) rows
        self._filtered_indices: list = []

        # The list of stored widgets
        self._filter_widgets = None

        # The ui containing save and load buttons
        self._save_load_buttons = None

        # The ui containing all the dropdown menus
        self._variable_selector = None

        # The ui containing all the input/output selector
        self._io_selector = None

        # The complete user interface
        self._ui = None

    def load(self, file_path: str | PathLike, file_formatter: IVariableIOFormatter = None):
        """
        Loads the file and stores its data.

        :param file_path: the path of file to interact with
        :param file_formatter: the formatter that defines file format. If not
                               provided, default format will be assumed.
        """

        self.file = file_path
        self.load_variables(VariableIO(file_path, file_formatter).read())

    def save(
        self, file_path: str | PathLike | None = None, file_formatter: IVariableIOFormatter = None
    ):
        """
        Save the dataframe to the file.

        :param file_path: the path of file to save. If not given, the initially
                          read file will be overwritten.
        :param file_formatter: the formatter that defines file format. If not
                               provided, default format will be assumed.
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
        self._create_io_selector()
        return self._render_sheet()

    def load_variables(
        self, variables: VariableList, attribute_to_column: dict[str, str] | None = None
    ):
        """
        Loads provided variable list and replace current data set.

        :param variables: the variables to load
        :param attribute_to_column: dictionary keys tell what variable attributes are kept
                                    and the values tell what name will be displayed. If
                                    not provided, default translation will apply.
        """

        if not attribute_to_column:
            attribute_to_column = VariableViewer._DEFAULT_COLUMN_RENAMING

        self.dataframe = (
            variables.to_dataframe()
            .rename(columns=attribute_to_column)[attribute_to_column.values()]
            .reset_index(drop=True)
        )

        self.dataframe["I/O"] = NA
        self.dataframe.loc[self.dataframe["is_input"] == 1, "I/O"] = INPUT
        self.dataframe.loc[self.dataframe["is_input"] == 0, "I/O"] = OUTPUT
        self.dataframe.drop(columns=["is_input"], inplace=True)

    def get_variables(self, column_to_attribute: dict[str, str] | None = None) -> VariableList:
        """

        :param column_to_attribute: dictionary keys tell what columns are kept and the values
                                    tell what variable attribute it corresponds to. If not
                                    provided, default translation will apply.
        :return: a variable list from current data set
        """
        if not column_to_attribute:
            column_to_attribute = {
                value: key for key, value in VariableViewer._DEFAULT_COLUMN_RENAMING.items()
            }

        dataframe = self.dataframe.copy()

        dataframe["is_input"] = None
        dataframe.loc[dataframe["I/O"] == INPUT, "is_input"] = True
        dataframe.loc[dataframe["I/O"] == OUTPUT, "is_input"] = False
        dataframe.drop(columns=["I/O"], inplace=True)
        return VariableList.from_dataframe(  # Variables
            dataframe[column_to_attribute.keys()].rename(columns=column_to_attribute)
        )

    @staticmethod
    def _value_to_display(value) -> str | float:
        """Convert a variable value to a grid-displayable scalar.

        Array values (numpy arrays or lists) are represented as a string so that
        ipydatagrid can serialize them without raising an inhomogeneous-shape error
        (the root cause of issue #596).
        """
        if isinstance(value, np.ndarray):
            return str(value.tolist())
        if isinstance(value, (list, tuple)):
            return str(list(value))
        return value

    @staticmethod
    def _display_to_value(display_value, original_value):
        """Parse a value coming back from the grid into the appropriate Python type.

        If the original value was an array-like (list, tuple, or numpy array),
        the edited string is parsed back into the same type.
        Otherwise a plain float conversion is attempted.
        """
        if isinstance(original_value, (list, tuple, np.ndarray)):
            try:
                parsed = ast.literal_eval(str(display_value))
                if isinstance(original_value, np.ndarray):
                    return np.array(parsed, dtype=float)
                return type(original_value)(parsed)
            except (ValueError, SyntaxError):
                return original_value
        try:
            return float(display_value)
        except (ValueError, TypeError):
            return display_value

    @staticmethod
    def _df_to_grid(df: pd.DataFrame) -> DataGrid:
        """
        Transforms a pandas DataFrame into an ipydatagrid DataGrid.

        Array values in the "Value" column are converted to their string
        representation so the grid can display them without serialization errors.

        :param df: the pandas DataFrame to be converted (may have non-contiguous index)
        :return: the DataGrid widget
        """
        if df.empty:
            return DataGrid(pd.DataFrame(), editable=True, layout=widgets.Layout(height="200px"))

        display_df = df.copy().reset_index(drop=True)
        if "Value" in display_df.columns:
            display_df["Value"] = display_df["Value"].apply(VariableViewer._value_to_display)

        return DataGrid(
            display_df,
            editable=True,
            layout=widgets.Layout(height="400px"),
            column_widths={"Name": 300, "Value": 100, "Unit": 80, "Description": 300, "I/O": 60},
        )

    def _update_df(self, cell: dict):
        """
        Callback for ipydatagrid ``on_cell_change``.  Updates ``self.dataframe``
        when the user edits the *Value* column.

        :param cell: dict with keys ``row``, ``column``, ``column_index``, ``value``
        """
        if cell["column"] != "Value":
            return

        grid_row = cell["row"]
        if grid_row >= len(self._filtered_indices):
            return

        original_idx = self._filtered_indices[grid_row]
        original_value = self.dataframe.loc[original_idx, "Value"]
        new_value = self._display_to_value(cell["value"], original_value)
        self.dataframe.loc[original_idx, "Value"] = new_value

    def _render_sheet(self) -> display:
        """
        Renders an interactive DataGrid with dropdown menus of the stored dataframe.

        :return display of the user interface
        """
        self._filter_widgets = []
        modules_item = [TAG_ALL, *sorted(self._find_submodules(self.dataframe))]
        w = widgets.Dropdown(options=modules_item)
        self._filter_widgets.append(w)
        return self._render_ui()

    def _update_items(self, change=None):
        """
        Updates the filter_widgets with respect to higher level filter_widgets values.
        """
        # 20 will never be reached
        for i in range(20):
            if i == 0:
                self._filter_widgets[0].observe(self._update_items, "value")
                self._filter_widgets[0].observe(self._update_variable_selector, "value")
            elif i <= len(self._filter_widgets):
                modules = [item.value for item in self._filter_widgets[0:i]]
                var_name = ":".join(modules)
                modules_item = sorted(self._find_submodules(self.dataframe, modules))
                if modules_item:
                    # Check if the item exists already
                    if i == len(self._filter_widgets):
                        if len(modules_item) > 1:
                            modules_item.insert(0, TAG_ALL)
                        widget = widgets.Dropdown(options=modules_item)
                        widget.observe(self._update_items, "value")
                        widget.observe(self._update_variable_selector, "value")
                        self._filter_widgets.append(widget)
                    else:
                        if (TAG_ALL not in modules_item) and (
                            len(modules_item) > 1 or var_name in self.dataframe["Name"].to_numpy()
                        ):
                            modules_item.insert(0, TAG_ALL)
                        self._filter_widgets[i].options = modules_item
                elif i < len(self._filter_widgets):
                    self._filter_widgets.pop(i)
            else:
                break

    def _update_variable_selector(self, change=None):
        """
        Updates the variable selector with respect to the
        actual filter_widgets stored.
        """
        items_box = widgets.HBox(self._filter_widgets)
        items_box = widgets.VBox([widgets.Label(value="Variable name"), items_box])
        self._variable_selector = items_box

    def _create_io_selector(self):
        """
        The dropdown menu enables to selector only inputs, only outputs or all variables.
        """
        io_selector = widgets.Dropdown(
            options=[TAG_ALL, "Inputs", "Outputs"], layout=widgets.Layout(width="auto")
        )
        io_selector.observe(self._render_ui, "value")

        self._io_selector = widgets.VBox([widgets.Label(value="I/O"), io_selector])

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

        items_box = widgets.HBox([load_button, save_button])

        self._save_load_buttons = items_box

    def _update_sheet(self):
        """
        Updates the grid after filtering the dataframe with respect to
        the actual values of the variable dropdown menus.
        """
        modules = [item.value for item in self._filter_widgets]
        io_value = self._io_selector.children[1].value
        if io_value == "Inputs":
            var_io_type = INPUT
        elif io_value == "Outputs":
            var_io_type = OUTPUT
        else:
            var_io_type = TAG_ALL

        filtered_var = self._filter_variables(self.dataframe, modules, var_io_type=var_io_type)

        # Store original indices so _update_df can map grid rows back to self.dataframe
        self._filtered_indices = filtered_var.index.tolist()

        self._grid = self._df_to_grid(filtered_var)
        self._grid.on_cell_change(self._update_df)

    def _render_ui(self, change=None) -> display:
        """
        Renders the dropdown menus for the variable selector and the corresponding
        DataGrid containing the variable info.

        :return the display object
        """
        self._update_items()
        self._update_variable_selector()
        self._update_sheet()
        for item in self._filter_widgets:
            item.observe(self._render_ui, "value")
        selectors = widgets.HBox([self._io_selector, self._variable_selector])

        if self._ui is not None:
            self._ui.children = [self._save_load_buttons, selectors, self._grid]
            return None

        self._ui = widgets.VBox([self._save_load_buttons, selectors, self._grid])
        return display(self._ui)

    @staticmethod
    def _find_submodules(df: pd.DataFrame, modules: list[str] | None = None) -> set[str]:
        """
        Search for submodules at root or provided modules.

        To find the submodules the method analyzes the name of the variables.
        If the kwarg 'modules' is not None, the submodules search will be applied to
        the variables that are part of these modules.

        :param df: the pandas dataframe containing the variables
        :param modules: the list of modules to which the variables belong
        :return the submodules list
        """
        var_names = df.filter(items=["Name"])

        if not modules:
            modules = []

        def get_next_module(path):
            submodules = path.split(":")
            if len(modules) >= len(submodules) or submodules[: len(modules)] != modules:
                return ""

            return submodules[len(modules)]

        submodules = pd.DataFrame.map(var_names, get_next_module)

        submodules = submodules[submodules.Name != ""]

        return set(submodules["Name"].tolist())

    @staticmethod
    def _filter_variables(
        df: pd.DataFrame, modules: list[str], var_io_type: str | None = None
    ) -> pd.DataFrame:
        """
        Returns a filtered dataframe with respect to a set of modules and variable type.

        The variables kept must be part of the modules list provided and the variable type
        'IN' or 'OUT'(if provided).

        :param df: the pandas dataframe containing the variables
        :param modules: the list of modules to which the variables belong
        :param var_io_type: the type of variables to keep
        :return the filtered dataframe
        """
        if var_io_type is None:
            var_io_type = TAG_ALL
        path = ""
        for _ in modules:
            path = ":".join(modules[:-1]) if modules[-1] == TAG_ALL else ":".join(modules)
        path_filter = df.Name.str.startswith(path)
        io_filter = pd.Series(
            [True] * len(df) if var_io_type == TAG_ALL else df["I/O"] == var_io_type
        )

        return df[path_filter & io_filter]  # Filtered_df
