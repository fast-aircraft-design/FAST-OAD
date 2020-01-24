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
import ipywidgets as widgets
from IPython.display import display
pd.set_option('display.max_rows', None)

from fastoad.io.configuration import FASTOADProblem
from fastoad.io.xml import OMXmlIO


class FASTOADDataFrame():

    def __init__(self):

        self.col_names = ['Module', 'Type', 'Name', 'Value', 'Unit', 'Description']

        self.df = pd.DataFrame()

        self._modules = {'TLAR': 'TLAR',
                         'aerodynamics': 'Aerodynamics',
                         'geometry': 'Geometry',
                         'weight': 'Mass Breakdown',
                         'propulsion': 'Propulsion'
        }

    def read_problem(self, problem: FASTOADProblem):
        problem_variables = {}
        inputs = problem.model._var_allprocs_prom2abs_list['input']
        outputs = problem.model._var_allprocs_prom2abs_list['output']
        problem_variables.update(inputs)
        problem_variables.update(outputs)

        system = problem.model

        module_names = [name for (name, module) in self._modules.items()]

        # Adding modules infos
        for prom_name, abs_names  in problem_variables.items():
            # We assume a variable can not be in two different module
            # Pick the first
            abs_name = abs_names[0]
            for module_name in module_names:
                if module_name in prom_name:
                    if prom_name in inputs:
                        var_type = 'Input'
                    else:
                        var_type = 'Output'
                    self.df = self.df.append([{'Module': self._modules[module_name],
                                               'Type': var_type,
                                               'Name': prom_name,
                                               'Value': problem[prom_name],
                                               'Unit': system._var_abs2meta[abs_name]['units'],
                                               'Description': system._var_abs2meta[abs_name]['desc']
                                               }
                                              ])[self.col_names]
        # Adding optimization infos
        opt_col_names = ['Module', 'Type', 'Name', 'Value', 'Lower', 'Upper', 'Unit', 'Description']
        driver = problem.driver
        for (abs_name, infos) in driver._designvars.items():
            prom_name = infos['name']
            self.df = self.df.append([{'Module': 'Optimization',
                                       'Type': 'Design Variable',
                                       'Name': prom_name,
                                       'Value': problem[prom_name],
                                       'Lower': infos['lower'],
                                       'Upper': infos['upper'],
                                       'Unit': system._var_abs2meta[abs_name]['units'],
                                       'Description': system._var_abs2meta[abs_name]['desc']
                                       }
                                      ])[opt_col_names]

        for (abs_name, infos) in driver._cons.items():
            prom_name = infos['name']
            self.df = self.df.append([{'Module': 'Optimization',
                                       'Type': 'Constraint',
                                       'Name': prom_name,
                                       'Value': problem[prom_name],
                                       'Lower': infos['lower'],
                                       'Upper': infos['upper'],
                                       'Unit': system._var_abs2meta[abs_name]['units'],
                                       'Description': system._var_abs2meta[abs_name]['desc']
                                       }
                                      ])[opt_col_names]

        for (abs_name, infos) in driver._objs.items():
            prom_name = infos['name']
            self.df = self.df.append([{'Module': 'Optimization',
                                       'Type': 'Objective',
                                       'Name': prom_name,
                                       'Value': problem[prom_name],
                                       'Lower': '-',
                                       'Upper': '-',
                                       'Unit': system._var_abs2meta[abs_name]['units'],
                                       'Description': system._var_abs2meta[abs_name]['desc']
                                       }
                                      ])[opt_col_names]

    def read_xml(self, aircraft_xml: OMXmlIO):
        pass

    def print(self):
        items = sorted(self.df['Module'].unique().tolist())
        def f(Type):
            return display(self.df[self.df['Module']==Type])
        widgets.interact(f, Type=items)
        return f