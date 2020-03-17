"""
Defines the data frame for postprocessing
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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
from typing import List
import pandas as pd
import ipysheet as sh
import ipywidgets as widgets
from IPython.display import display, clear_output

from fastoad.io.serialize import AbstractOMFileIO
from fastoad.openmdao.connections_utils import get_variables_from_ivc, \
    get_variables_from_df, get_df_from_variables, get_ivc_from_variables

pd.set_option('display.max_rows', None)


class VariableViewer:
    """
    A class for interacting with FAST-OAD file files.
    The file file data is stored in a pandas DataFrame. The class built so that a modification
    of the DataFrame is instantly replicated on the file file.
    The interaction is achieved using a user interface built with widgets from ipywidgets and
    Sheets from ipysheet.

    A classical usage of this class will be::

        df = VariableViewer()  # instantiation of dataframe
        file = AbstractOMFileIO('problem_outputs.file') #  instantiation of file io
        df.load(file)  # load the file
        df.display()  # renders a ui for reading/modifying the file
    """

    def __init__(self):

        # The file file to be set
        self.file = None

        # The dataframe which is the mirror of the file file
        self.dataframe = pd.DataFrame()

        # The sheet which is the mirror of the dataframe
        self.sheet = None

        # The list of stored widgets
        self.filter_widgets = None

        # The ui containing all the dropdown menus
        self.variable_selector = None

        # A tag used to select all submodules
        self.all_tag = '--ALL--'

        # Max depth when searching for submodules
        self.max_depth = None

    def load(self, file: AbstractOMFileIO):
        """
        Loads the file file and stores it in a dataframe.

        :param file: the file file to interact with
        """
        self.file = file
        self.dataframe = self.file_to_df(self.file)
        self.dataframe = self.dataframe.reset_index(drop=True)

    def save(self, file: AbstractOMFileIO):
        """
        Save the dataframe to the file file.

        :param file: the file file to save
        """
        self.df_to_file(self.dataframe, file)

    def display(self):
        """
        Displays the datasheet
        :return display of the user interface:
        """
        return self._render_sheet()

    @staticmethod
    def file_to_df(file: AbstractOMFileIO) -> pd.DataFrame:
        """
        Returns the equivalent pandas dataframe of the file.

        :param file: the file to convert
        :return the equivalent dataframe
        """
        # TODO: should we add a 'Type' field if we decide to add a type attribute to Variable ?
        # Read the file
        ivc = file.read()

        # Extract the variables list
        variables = get_variables_from_ivc(ivc)
        # pylint: disable=invalid-name # that's a common naming
        df = get_df_from_variables(variables)

        return df

    # pylint: disable=invalid-name # that's a common naming
    @staticmethod
    def df_to_file(df: pd.DataFrame, file: AbstractOMFileIO):
        """
        Returns the equivalent file of the pandas dataframe .

        :param df: the dataframe to convert
        :param file: the resulting file
        """
        # Extract the variables list
        variables = get_variables_from_df(df)
        ivc = get_ivc_from_variables(variables)
        file.write(ivc)

    # pylint: disable=invalid-name # that's a common naming
    @staticmethod
    def df_to_sheet(df: pd.DataFrame) -> sh.Sheet:
        """
        Transforms a pandas DataFrame into a ipysheet Sheet.
        The cells are set to read only except for the values.

        :param df: the pandas DataFrame to be converted
        :return the equivalent ipysheet Sheet
        """
        if not df.empty:
            sheet = sh.from_dataframe(df)
            column = df.columns.get_loc('Value')

            for cell in sheet.cells:
                if column not in (cell.column_start, cell.column_end):
                    cell.read_only = True
                else:
                    cell.type = 'numeric'
                    # TODO: make the number of decimals depnd on the module ?
                    # or chosen in the ui by the user
                    cell.numeric_format = '0.000'

            # Name, Value, Unit, Description
            sheet.column_width = [150, 50, 20, 150]

        else:
            sheet = sh.sheet()
        return sheet

    @staticmethod
    def sheet_to_df(sheet: sh.Sheet) -> pd.DataFrame:
        """
        Transforms a ipysheet Sheet into a pandas DataFrame.

        :param sheet: the ipysheet Sheet to be converted
        :return the equivalent pandas DataFrame
        """
        df = sh.to_dataframe(sheet)
        return df

    # pylint: disable=unused-argument  # args has to be there for observe() to work
    def _update_df(self, *args):
        """
        Updates the stored DataFrame with respect to the actual values of the Sheet.
        Then updates the file with respect to the stored DataFrame.
        """
        df = self.sheet_to_df(self.sheet)
        for i in df.index:
            self.dataframe.loc[int(i), :] = df.loc[i, :].values

    # pylint: disable=unused-argument  # args has to be there for observe() to work
    def _update_file(self, *args):
        """
        Updates the variables values and attributes in the file with respect to the
        actual values of the stored DataFrame .
        """
        self.df_to_file(self.dataframe, self.file)

    def _render_sheet(self, max_depth: int = 6) -> display:
        """
        Renders an interactive pysheet with dropdown menus of the stored dataframe.

        :param max_depth: the maximum depth when searching submodules
        :return display of the user interface
        """
        self.max_depth = max_depth
        self.filter_widgets = []
        modules_item = sorted(self._find_submodules(self.dataframe))
        if modules_item:
            w = widgets.Dropdown(options=modules_item)
            self.filter_widgets.append(w)
        return self._render_ui()

    # pylint: disable=unused-argument  # args has to be there for observe() to work
    def _update_items(self, *args):
        """
        Updates the filter_widgets with respect to higher level filter_widgets values with
        a limited depth of self.max_depth.
        """
        for i in range(self.max_depth):
            if i == 0:
                self.filter_widgets[0].observe(self._update_items, 'value')
                self.filter_widgets[0].observe(self._update_variable_selector, 'value')
            elif i <= len(self.filter_widgets):
                modules = [item.value for item in self.filter_widgets[0:i]]
                modules_item = sorted(self._find_submodules(self.dataframe, modules))
                if modules_item:
                    # Check if the item exists already
                    if i == len(self.filter_widgets):
                        if len(modules_item) > 1:
                            modules_item.insert(0, self.all_tag)
                        widget = widgets.Dropdown(options=modules_item)
                        widget.observe(self._update_items, 'value')
                        widget.observe(self._update_variable_selector, 'value')
                        self.filter_widgets.append(widget)
                    else:
                        if (self.all_tag not in modules_item) and (len(modules_item) > 1):
                            modules_item.insert(0, self.all_tag)
                        self.filter_widgets[i].options = modules_item
                else:
                    if i < len(self.filter_widgets):
                        self.filter_widgets.pop(i)
            else:
                break

    # pylint: disable=unused-argument  # args has to be there for observe() to work
    def _update_variable_selector(self, *args):
        """
        Updates the variable selector with respect to the
        actual filter_widgets stored.
        """
        items_box = widgets.HBox(self.filter_widgets)
        items_box = widgets.VBox([widgets.Label(value='Variable name'),
                                  items_box])
        self.variable_selector = items_box

    def _update_sheet(self):
        """
        Updates the sheet after filtering the dataframe with respect to
        the actual values of the variable dropdown menus.
        """
        modules = [item.value for item in self.filter_widgets]

        filtered_var = self._filter_variables(self.dataframe, modules, var_type=None)

        self.sheet = self.df_to_sheet(filtered_var)

        for cell in self.sheet.cells:
            cell.observe(self._update_df, 'value')

    # pylint: disable=unused-argument  # args has to be there for observe() to work
    def _render_ui(self, *args) -> display:
        """
        Renders the dropdown menus for the variable selector and the corresponding
        ipysheet Sheet containing the variable infos.

        :return the display object
        """
        clear_output(wait=True)
        self._update_items()
        self._update_variable_selector()
        self._update_sheet()
        for item in self.filter_widgets:
            item.observe(self._render_ui, 'value')
        self.sheet.layout.height = '400px'
        ui = widgets.VBox([self.variable_selector, self.sheet])
        return display(ui)

    @staticmethod
    def _find_submodules(df: pd.DataFrame, modules: List[str] = None) -> List[str]:
        """
        Search for submodules at root or provided modules.

        To find the submodules the method analyzes the name of the variables.
        If the kwarg 'modules' is not None, the submodules search will be applied to
        the variables that are part of these modules.

        :param df: the pandas dataframe containing the variables
        :param modules: the list of modules to which the variables belong
        :return the submodules list
        """
        var_names = df.filter(items=['Name'])

        if not modules:
            modules = []

        def get_next_module(path):
            submodules = path.split(':')
            if len(modules) >= len(submodules) or submodules[:len(modules)] != modules:
                return ''
            else:
                return submodules[len(modules)]

        submodules = var_names.applymap(get_next_module)
        submodules = submodules[submodules.Name != '']

        return set(submodules['Name'].tolist())

    def _filter_variables(self, df: pd.DataFrame,
                          modules: List[str],
                          var_type: str = None) -> pd.DataFrame:
        """
        Returns a filtered dataframe with respect to a set of modules and variable type.

        The variables kept must be part of the modules list provided and the variable type
        'INPUT' or 'OUTPUT (if provided).

        :param df: the pandas dataframe containing the variables
        :param modules: the list of modules to which the variables belong
        :param var_type: the type of variables to keep
        :return the filtered dataframe
        """
        if var_type is None:
            var_type = self.all_tag
        path = ''
        for _ in modules:
            if modules[-1] == self.all_tag:
                path = ':'.join(modules[:-1])
            else:
                path = ':'.join(modules)

        var_names = df['Name'].unique().tolist()

        filtered_df = pd.DataFrame()

        for var_name in var_names:
            if path in var_name:
                if var_type == self.all_tag:
                    element = df[df['Name'] == var_name]
                    filtered_df = filtered_df.append(element)
                else:
                    element = df[(df['Name'] == var_name) & (df['Type'] == var_type)]
                    filtered_df = filtered_df.append(element)

        return filtered_df
