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

from os import PathLike
from typing import Dict, List, Set, Union

import ipysheet as sh
import ipywidgets as widgets
import pandas as pd
from IPython.display import display

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
    Sheets from ipysheet.

    A classical usage of this class will be::

        df = VariableViewer()  # instantiation of dataframe
        file = AbstractOMFileIO('problem_outputs.file') #  instantiation of file io
        df.load(file)  # load the file
        df.display()  # renders a ui for reading/modifying the file
    """

    # When getting a dataframe from a VariableList, the dictionary keys tell
    # what columns are kept and the values tell what name will be displayed.
    _DEFAULT_COLUMN_RENAMING = {
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

        # The sheet which is the mirror of the dataframe
        self._sheet = None

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

    def load(self, file_path: Union[str, PathLike], file_formatter: IVariableIOFormatter = None):
        """
        Loads the file and stores its data.

        :param file_path: the path of file to interact with
        :param file_formatter: the formatter that defines file format. If not
                               provided, default format will be assumed.
        """

        self.file = file_path
        self.load_variables(VariableIO(file_path, file_formatter).read())

    def save(
        self, file_path: Union[str, PathLike] = None, file_formatter: IVariableIOFormatter = None
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

    def load_variables(self, variables: VariableList, attribute_to_column: Dict[str, str] = None):
        """
        Loads provided variable list and replace current data set.

        :param variables: the variables to load
        :param attribute_to_column: dictionary keys tell what variable attributes are kept
                                    and the values tell what name will be displayed. If
                                    not provided, default translation will apply.
        """

        if not attribute_to_column:
            attribute_to_column = self._DEFAULT_COLUMN_RENAMING

        self.dataframe = (
            variables.to_dataframe()
            .rename(columns=attribute_to_column)[attribute_to_column.values()]
            .reset_index(drop=True)
        )

        self.dataframe["I/O"] = NA
        self.dataframe.loc[self.dataframe["is_input"] == 1, "I/O"] = INPUT
        self.dataframe.loc[self.dataframe["is_input"] == 0, "I/O"] = OUTPUT
        self.dataframe.drop(columns=["is_input"], inplace=True)

    def get_variables(self, column_to_attribute: Dict[str, str] = None) -> VariableList:
        """

        :param column_to_attribute: dictionary keys tell what columns are kept and the values
                                    tell what variable attribute it corresponds to. If not
                                    provided, default translation will apply.
        :return: a variable list from current data set
        """
        if not column_to_attribute:
            column_to_attribute = {
                value: key for key, value in self._DEFAULT_COLUMN_RENAMING.items()
            }

        dataframe = self.dataframe.copy()

        dataframe["is_input"] = None
        dataframe.loc[dataframe["I/O"] == INPUT, "is_input"] = True
        dataframe.loc[dataframe["I/O"] == OUTPUT, "is_input"] = False
        dataframe.drop(columns=["I/O"], inplace=True)
        variables = VariableList.from_dataframe(
            dataframe[column_to_attribute.keys()].rename(columns=column_to_attribute)
        )
        return variables

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
            column = df.columns.get_loc("Value")

            for cell in sheet.cells:
                if column not in (cell.column_start, cell.column_end):
                    cell.read_only = True
                else:
                    cell.type = "numeric"
                    # TODO: make the number of decimals depend on the module ?
                    # or chosen in the ui by the user
                    cell.numeric_format = "0.000"

            # Name, Value, Unit, Description
            sheet.column_width = [150, 50, 20, 150]

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
        df = self._sheet_to_df(self._sheet)
        for i in df.index:
            self.dataframe.loc[int(i), :] = df.loc[i, :].values

    def _render_sheet(self) -> display:
        """
        Renders an interactive pysheet with dropdown menus of the stored dataframe.

        :return display of the user interface
        """
        self._filter_widgets = []
        modules_item = [TAG_ALL] + sorted(self._find_submodules(self.dataframe))
        w = widgets.Dropdown(options=modules_item)
        self._filter_widgets.append(w)
        return self._render_ui()

    # pylint: disable=unused-argument  # args has to be there for observe() to work
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
                            len(modules_item) > 1 or var_name in self.dataframe["Name"].values
                        ):
                            modules_item.insert(0, TAG_ALL)
                        self._filter_widgets[i].options = modules_item
                else:
                    if i < len(self._filter_widgets):
                        self._filter_widgets.pop(i)
            else:
                break

    # pylint: disable=unused-argument  # args has to be there for observe() to work
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
        Updates the sheet after filtering the dataframe with respect to
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

        self._sheet = self._df_to_sheet(filtered_var)

        for cell in self._sheet.cells:
            cell.observe(self._update_df, "value")

    # pylint: disable=unused-argument  # args has to be there for observe() to work
    def _render_ui(self, change=None) -> display:
        """
        Renders the dropdown menus for the variable selector and the corresponding
        ipysheet Sheet containing the variable info.

        :return the display object
        """
        self._update_items()
        self._update_variable_selector()
        self._update_sheet()
        for item in self._filter_widgets:
            item.observe(self._render_ui, "value")
        self._sheet.layout.height = "400px"
        selectors = widgets.HBox([self._io_selector, self._variable_selector])

        if self._ui is not None:
            self._ui.children = [self._save_load_buttons, selectors, self._sheet]
            return None

        self._ui = widgets.VBox([self._save_load_buttons, selectors, self._sheet])
        return display(self._ui)

    @staticmethod
    def _find_submodules(df: pd.DataFrame, modules: List[str] = None) -> Set[str]:
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

        submodules = var_names.applymap(get_next_module)
        submodules = submodules[submodules.Name != ""]

        return set(submodules["Name"].tolist())

    @staticmethod
    def _filter_variables(
        df: pd.DataFrame, modules: List[str], var_io_type: str = None
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
            if modules[-1] == TAG_ALL:
                path = ":".join(modules[:-1])
            else:
                path = ":".join(modules)
        path_filter = df.Name.str.startswith(path)
        io_filter = [True] * len(df) if var_io_type == TAG_ALL else df["I/O"] == var_io_type

        filtered_df = df[path_filter & io_filter]

        return filtered_df
