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

pd.set_option('display.max_rows', None)

from fastoad.io.configuration import FASTOADProblem
from fastoad.io.xml import OMXmlIO
from fastoad.openmdao.connections_utils import get_variables_of_ivc_components


class FASTOADDataFrame():

    def __init__(self):

        self.col_names_variables = ['Type', 'Name',
                                    'Value', 'Unit', 'Description']

        self.col_names_optimization = ['Type', 'Name', 'Value',
                                       'Lower', 'Upper', 'Unit', 'Description']

        self.df_variables = pd.DataFrame()

        self.df_optimization = pd.DataFrame()

        self.all_tag = '--ALL--'

    def read_problem(self, problem: FASTOADProblem):
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
            self.df_variables = self.df_variables.append([{'Type': var_type,
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

            self.df_optimization = self.df_optimization.append([{'Type': 'Design Variable',
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

            self.df_optimization = self.df_optimization.append([{'Type': 'Constraint',
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

            self.df_optimization = self.df_optimization.append([{'Type': 'Objective',
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

    def read_xml(self, aircraft_xml: OMXmlIO):
        pass

    def data_sheet(self, max_depth=6):

        df_variables = self.df_variables

        items = []
        modules_item = sorted(self._find_submodules(df_variables))
        if modules_item:
            w = widgets.Dropdown(options=modules_item)
            items.append(w)

        w_type = widgets.Dropdown(options=[self.all_tag, 'Input', 'Output'],
                                  layout=widgets.Layout(width='auto'))

        def update_items(*args):
            for i in range(max_depth):
                if i == 0:
                    items[0].observe(update_items, 'value')
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
                                w.observe(update_items, 'value')
                                items.append(w)
                            else:
                                if (self.all_tag not in modules_item) and (len(modules_item) > 1):
                                    modules_item.insert(0, self.all_tag)
                                items[i].options = modules_item
                        else:
                            if i < len(items):
                                items.pop(i)
            return items

        def print_sheet(**kwargs):
            # Get variable type and remove
            var_type = kwargs['Type']
            del kwargs['Type']
            # Build list of items
            kwargs = [module for module in kwargs.values()]
            modules = kwargs
            filtered_var = self._filter_variables(self.df_variables, modules, var_type=var_type)
            sheet = self._build_sheet(filtered_var)
            return display(sheet)

        def render(*args):
            clear_output(wait=True)
            items = update_items()
            for item in items:
                item.observe(render, 'value')
            w_type.observe(render, 'value')
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
            out = widgets.interactive_output(print_sheet, kwargs)
            display(ui, out)

        return render()

    def _build_sheet(self, df):
        if not df.empty:
            sheet = sh.from_dataframe(df)
            column = df.columns.get_loc('Value')

            for cell in sheet.cells:
                if cell.column_start != column and cell.column_end != column:
                    cell.read_only = True

        else:
            sheet = sh.sheet()

        return sheet

    def _find_submodules(self, df, modules=None):
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

    def _filter_variables(self, df, modules, var_type=None):
        if var_type is None:
            var_type = self.all_tag
        path = ''
        for i in range(len(modules)):
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
