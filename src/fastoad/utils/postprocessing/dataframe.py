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
from IPython.display import display

pd.set_option('display.max_rows', None)

from fastoad.io.configuration import FASTOADProblem
from fastoad.io.xml import OMXmlIO
from fastoad.openmdao.connections_utils import get_unconnected_input_names, \
    get_variables_of_ivc_components


class FASTOADDataFrame():

    def __init__(self):

        self.col_names_variables = ['Module', 'Type', 'Name',
                                    'Value', 'Unit', 'Description']

        self.col_names_optimization = ['Module', 'Type', 'Name', 'Value',
                                       'Lower', 'Upper', 'Unit', 'Description']

        self.df_variables = pd.DataFrame()

        self.df_optimization = pd.DataFrame()

        self._modules = {'TLAR': 'TLAR',
                         'aerodynamics': 'Aerodynamics',
                         'geometry': 'Geometry',
                         'weight': 'Mass Breakdown',
                         'propulsion': 'Propulsion'
                         }

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

        module_names = [name for (name, module) in self._modules.items()]

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
            for module_name in module_names:
                if module_name in prom_name:
                    if prom_name in input_names:
                        var_type = 'Input'
                    else:
                        var_type = 'Output'
                    self.df_variables = self.df_variables.append([{'Module': self._modules[module_name],
                                                                   'Type': var_type,
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

            self.df_optimization = self.df_optimization.append([{'Module': 'Optimization',
                                                                 'Type': 'Design Variable',
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

            self.df_optimization = self.df_optimization.append([{'Module': 'Optimization',
                                                                 'Type': 'Constraint',
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

            self.df_optimization = self.df_optimization.append([{'Module': 'Optimization',
                                                                 'Type': 'Objective',
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

    def print(self):
        items_var = self.df_variables['Module'].unique().tolist()
        items_opt = self.df_optimization['Module'].unique().tolist()
        items = sorted(items_var + items_opt)

        def f(Type):
            if Type == 'Optimization':
                df = display(self.df_optimization[
                                 self.df_optimization['Module'] == Type])
            else:
                df = display(self.df_variables[
                                 self.df_variables['Module'] == Type])
            return df

        widgets.interact(f, Type=items)
        return f

    def data_sheet(self, include_inputs=True, include_outputs=True):
        items_var = self.df_variables['Module'].unique().tolist()
        items_opt = self.df_optimization['Module'].unique().tolist()
        items = sorted(items_var + items_opt)
        if not include_outputs:
            df_optimization = self.df_optimization[
                self.df_optimization['Type'] == 'Input']
            df_variables = self.df_variables[
                self.df_variables['Type'] == 'Input']
        elif not include_inputs:
            df_optimization = self.df_optimization[
                self.df_optimization['Type'] == 'Output']
            df_variables = self.df_variables[
                self.df_variables['Type'] == 'Output']
        else:
            df_optimization = self.df_optimization
            df_variables = self.df_variables

        def f(Type):
            if Type == 'Optimization':
                df = display(self.build_sheet(df_optimization[
                                                  df_optimization['Module'] == Type]))
            else:
                df = display(self.build_sheet(df_variables[
                                                  df_variables['Module'] == Type]))
            return df

        widgets.interact(f, Type=items)
        return f

    def build_sheet(self, df):

        sheet = sh.from_dataframe(df)
        column = df.columns.get_loc('Value')

        for cell in sheet.cells:
            if cell.column_start != column and cell.column_end != column:
                cell.read_only = True

        return sheet
