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
import numpy as np
import pandas as pd
import ipysheet as sh
import ipywidgets as widgets
from IPython.display import display, clear_output

from fastoad.io.configuration import FASTOADProblem
from fastoad.io.xml import OMXmlIO
from fastoad.openmdao.connections_utils import get_variables_from_ivc, \
    get_variables_of_ivc_components, get_variables_from_df, \
    get_df_from_variables

pd.set_option('display.max_rows', None)


class FASTOADDataFrame:

    def __init__(self):

        self.col_names_variables = ['Type', 'Name',
                                    'Value', 'Unit', 'Description']

        self.col_names_optimization = ['Type', 'Name', 'Value',
                                       'Lower', 'Upper', 'Unit', 'Description']

        self.df_variables = pd.DataFrame()

        self.df_optimization = pd.DataFrame()

        self.all_tag = '--ALL--'

        self.sheet = None
        self.items = None
        self.variable_selector = None
        self.out = None

    def update_df(self, *args):
        df = self.sheet_to_df(self.sheet)
        self._update_df(df)

    def read_problem(self, problem: FASTOADProblem):
        """
        Reads a FASTOADProblem instance and stores it in two separate dataframes (variables
        and optimization).

        :param problem:
        """
        problem_variables = {}
        variables = get_variables_of_ivc_components(problem)
        input_names = [var.name for var in variables]
        filtered_inputs = {}

        outputs = problem.model._var_allprocs_prom2abs_list['output']
        for prom_name, abs_names in outputs.items():
            if prom_name in input_names:
                filtered_inputs[prom_name] = abs_names

        problem_variables.update(filtered_inputs)
        problem_variables.update(outputs)

        system = problem.model

        # Adding modules infos
        for prom_name, abs_names in problem_variables.items():
            # We assume a variable can not be in two different module
            # Pick the first
            abs_name = abs_names[0]
            value = problem[prom_name]
            if len(value) == 1:
                value = np.asscalar(value)
            else:
                value = np.ndarray.tolist(value)

            if prom_name in input_names:
                var_type = 'Input'
            else:
                var_type = 'Output'
            self.df_variables = \
                self.df_variables.append([{'Type': var_type,
                                           'Name': prom_name,
                                           'Value': value,
                                           'Unit': system._var_abs2meta[abs_name]['units'],
                                           'Description': system._var_abs2meta[abs_name]['desc']
                                           }
                                          ])[self.col_names_variables]
        # Adding optimization infos
        driver = problem.driver
        for (abs_name, infos) in driver._designvars.items():
            prom_name = infos['name']
            value = problem[prom_name]
            if len(value) == 1:
                value = np.asscalar(value)
            else:
                value = np.ndarray.tolist(value)

            self.df_optimization = \
                self.df_optimization.append([{'Type': 'Design Variable',
                                              'Name': prom_name,
                                              'Value': value,
                                              'Lower': infos['lower'],
                                              'Upper': infos['upper'],
                                              'Unit': system._var_abs2meta[abs_name]['units'],
                                              'Description': system._var_abs2meta[abs_name]['desc']
                                              }
                                             ])[self.col_names_optimization]

        for (abs_name, infos) in driver._cons.items():
            prom_name = infos['name']
            value = problem[prom_name]
            if len(value) == 1:
                value = np.asscalar(value)
            else:
                value = np.ndarray.tolist(value)

            self.df_optimization = \
                self.df_optimization.append([{'Type': 'Constraint',
                                              'Name': prom_name,
                                              'Value': value,
                                              'Lower': infos['lower'],
                                              'Upper': infos['upper'],
                                              'Unit': system._var_abs2meta[abs_name]['units'],
                                              'Description': system._var_abs2meta[abs_name]['desc']
                                              }
                                             ])[self.col_names_optimization]

        for (abs_name, infos) in driver._objs.items():
            prom_name = infos['name']
            value = problem[prom_name]
            if len(value) == 1:
                value = np.asscalar(value)
            else:
                value = np.ndarray.tolist(value)

            self.df_optimization = \
                self.df_optimization.append([{'Type': 'Objective',
                                              'Name': prom_name,
                                              'Value': value,
                                              'Lower': '-',
                                              'Upper': '-',
                                              'Unit': system._var_abs2meta[abs_name]['units'],
                                              'Description': system._var_abs2meta[abs_name]['desc']
                                              }
                                             ])[self.col_names_optimization]

        self.df_variables = self.df_variables.reset_index(drop=True)
        self.df_optimization = self.df_optimization.reset_index(drop=True)

    def update_problem(self, problem: FASTOADProblem) -> FASTOADProblem:
        """
        Updates a FASTOADProblem with actual values of the dataframe.

        :param problem:
        :return updated problem
        """
        pass

    def read_xml(self, aircraft_xml: OMXmlIO):
        """
        Reads a xml file and stores it in two separate dataframes
        (variables and optimization).

        :param aircraft_xml:
        """
        pass

    def data_sheet(self, max_depth: int = 6) -> display:
        """
        Renders an interactive pysheet with dropdown menus of the stored dataframe.

        :param max_depth: the maximum depth when searching submodules
        :return display of the user interface
        """

        df_variables = self.df_variables

        items = []
        modules_item = sorted(self._find_submodules(df_variables))
        if modules_item:
            w = widgets.Dropdown(options=modules_item)
            items.append(w)

        w_type = widgets.Dropdown(options=[self.all_tag, 'Input', 'Output'],
                                  layout=widgets.Layout(width='auto'))

        def _update_items(*args):
            for i in range(max_depth):
                if i == 0:
                    items[0].observe(_update_items, 'value')
                else:
                    if i <= len(items):
                        modules = [item.value for item in items[0:i]]
                        modules_item = sorted(self._find_submodules(df_variables, modules))
                        if modules_item:
                            # Check if the item exists already
                            if i == len(items):
                                if len(modules_item) > 1:
                                    modules_item.insert(0, self.all_tag)
                                w = widgets.Dropdown(options=modules_item)
                                w.observe(_update_items, 'value')
                                items.append(w)
                            else:
                                if (self.all_tag not in modules_item) and (len(modules_item) > 1):
                                    modules_item.insert(0, self.all_tag)
                                items[i].options = modules_item
                        else:
                            if i < len(items):
                                items.pop(i)
            return items

        def _print_sheet(**kwargs):
            # Get variable type and remove
            var_type = kwargs['Type']
            del kwargs['Type']
            # Build list of items
            kwargs = [module for module in kwargs.values()]
            modules = kwargs
            filtered_var = self._filter_variables(self.df_variables, modules, var_type=var_type)
            sheet = self.df_to_sheet(filtered_var)
            return display(sheet)

        def _render(*args):
            clear_output(wait=True)
            items = _update_items()
            for item in items:
                item.observe(_render, 'value')
            w_type.observe(_render, 'value')
            type_box = widgets.VBox([widgets.Label(value='Type'),
                                     w_type],
                                    layout=widgets.Layout(width='auto'))
            items_box = widgets.HBox(items)
            items_box = widgets.VBox([widgets.Label(value='Variable name'),
                                      items_box])
            ui = widgets.HBox([type_box, items_box])

            kwargs = {}

            i = 0
            for item in items:
                kwargs[str(i)] = item
                i += 1
            kwargs['Type'] = w_type
            out = widgets.interactive_output(_print_sheet, kwargs)
            display(ui, out)

        return _render()

    def render_sheet(self, max_depth: int = 6) -> display:
        """
        Renders an interactive pysheet with dropdown menus of the stored dataframe.

        :param max_depth: the maximum depth when searching submodules
        :return display of the user interface
        """
        self.max_depth = max_depth
        self.items = []
        modules_item = sorted(self._find_submodules(self.df_variables))
        if modules_item:
            w = widgets.Dropdown(options=modules_item)
            self.items.append(w)
        return self._render_ui()

    def _update_items(self, *args):
        """
        Updates the items with respect to higher level items values with
        a limited depth of self.max_depth.
        """
        for i in range(self.max_depth):
            if i == 0:
                self.items[0].observe(self._update_items, 'value')
                self.items[0].observe(self._update_variable_selector, 'value')
            else:
                if i <= len(self.items):
                    modules = [item.value for item in self.items[0:i]]
                    modules_item = sorted(self._find_submodules(self.df_variables, modules))
                    if modules_item:
                        # Check if the item exists already
                        if i == len(self.items):
                            if len(modules_item) > 1:
                                modules_item.insert(0, self.all_tag)
                            w = widgets.Dropdown(options=modules_item)
                            w.observe(self._update_items, 'value')
                            w.observe(self._update_variable_selector, 'value')
                            self.items.append(w)
                        else:
                            if (self.all_tag not in modules_item) and (len(modules_item) > 1):
                                modules_item.insert(0, self.all_tag)
                            self.items[i].options = modules_item
                    else:
                        if i < len(self.items):
                            self.items.pop(i)

    def _update_variable_selector(self, *args):
        """
        Updates the variable selector with respect to the
        actual items stored.
        """
        items_box = widgets.HBox(self.items)
        items_box = widgets.VBox([widgets.Label(value='Variable name'),
                                  items_box])
        self.variable_selector = items_box

    def _update_sheet(self):
        """
        Updates the sheet after filtering the dataframe with respect to
        the actual values of the variable dropdown menus.
        """
        modules = [item.value for item in self.items]

        filtered_var = self._filter_variables(self.df_variables, modules, var_type=None)

        self.sheet = self.df_to_sheet(filtered_var)

        for cell in self.sheet.cells:
            cell.observe(self.update_df, 'value')

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
        for item in self.items:
            item.observe(self._render_ui, 'value')
        return display(self.variable_selector, self.sheet)

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
                if cell.column_start != column and cell.column_end != column:
                    cell.read_only = True

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

    def _update_df(self, df):
        for i in df.index:
            self.df_variables.loc[int(i), :] = df.loc[i, :].values

    @staticmethod
    def _find_submodules(df: pd.DataFrame, modules: [str] = None) -> [str]:
        """
        Search for submodules at root or provided modules.

        To find the submodules the method analyzes the name of the variables.
        If the kwarg 'modules' is not None, the submodules search will be applied to
        the variables that are part of these modules.

        :param df: the pandas dataframe containing the variables
        :param modules: the list of modules to which the variables belong
        :return the submodules list
        """
        var_names = df['Name'].unique().tolist()

        submodules = set()

        for var_name in var_names:
            full_submodules = var_name.split(':')
            if modules is not None:
                if all(module in full_submodules for module in modules):
                    module_idx = full_submodules.index(modules[-1])
                    if module_idx < len(full_submodules) - 1:
                        submodules.add(full_submodules[module_idx + 1])
            else:
                submodules.add(full_submodules[0])

        submodules = list(submodules)
        return submodules

    def _filter_variables(self, df: pd.DataFrame,
                          modules: [str],
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
        for i, module in enumerate(modules):
            module = modules[i]
            if module != self.all_tag:
                if i < len(modules) - 1:
                    path += module + ':'
                else:
                    path += module

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

    def xml_interact(self, xml: OMXmlIO):
        """
        Renders an interactive pysheet with dropdown menus of the xml file.

        :param xml_file: the xml file to interact with
        :return display of the user interface
        """

        self.df_variables = self.xml_to_df(xml)
        self.df_variables = self.df_variables.reset_index(drop=True)

        return self.render_sheet()

    @staticmethod
    def xml_to_df(xml: OMXmlIO) -> pd.DataFrame:
        """
        Returns the equivalent pandas dataframe of the xml file.

        :param xml: the xml file to convert
        :return the equivalent dataframe
        """
        # TODO: should we add a 'Type' field if we decide to add a type attribute to Variable ?
        col_names = ['Name', 'Value', 'Unit', 'Description']
        df = pd.DataFrame()

        # Read the xml
        ivc = xml.read()

        # Extract the variables list
        variables = get_variables_from_ivc(ivc)
        df = get_df_from_variables(variables)

        return df
