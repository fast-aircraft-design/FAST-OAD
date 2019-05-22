"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

#      This file is part of FAST : A framework for rapid Overall Aircraft Design
#      Copyright (C) 2019  ONERA/ISAE
#      FAST is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent


class LinkWeightVariables(ExplicitComponent):

    def initialize(self):
        airframe_names = ['A1', 'A2', 'A31', 'A32', 'A4', 'A51', 'A52', 'A6', 'A7']
        propulsion_names = ['B1', 'B2', 'B3']
        systems_names = ['C11', 'C12', 'C13', 'C21', 'C22', 'C23', 'C24', 'C25',
                         'C26', 'C27', 'C3', 'C4', 'C51', 'C52', 'C6']
        furniture_names = ['D1', 'D2', 'D3', 'D4', 'D5']

        self.options.declare('airframe_names', default=airframe_names, types=list)
        self.options.declare('propulsion_names', default=propulsion_names, types=list)
        self.options.declare('systems_names', default=systems_names, types=list)
        self.options.declare('furniture_names', default=furniture_names, types=list)

    def setup(self):
        self.airframe_names = self.options['airframe_names']
        self.propulsion_names = self.options['propulsion_names']
        self.systems_names = self.options['systems_names']
        self.furniture_names = self.options['furniture_names']

        for name in range(len(self.airframe_names)):
            self.add_input('weight_airframe:' + self.airframe_names[name], val=np.nan)

        for name in range(len(self.propulsion_names)):
            self.add_input('weight_propulsion:' + self.propulsion_names[name], val=np.nan)

        for name in range(len(self.systems_names)):
            self.add_input('weight_systems:' + self.systems_names[name], val=np.nan)

        for name in range(len(self.furniture_names)):
            self.add_input('weight_furniture:' + self.furniture_names[name], val=np.nan)

        self.add_input('weight_crew:E', val=np.nan)

        self.add_output('weight_airframe:A')
        self.add_output('weight_propulsion:B')
        self.add_output('weight_systems:C')
        self.add_output('weight_furniture:D')
        self.add_output('weight:OEW')

    def compute(self, inputs, outputs):
        # Airframe
        weight_A = []
        weight_B = []
        weight_C = []
        weight_D = []

        for name in range(len(self.airframe_names)):
            weight_A.append(inputs['weight_airframe:' + self.airframe_names[name]][0])

        for name in range(len(self.propulsion_names)):
            weight_B.append(inputs['weight_propulsion:' + self.propulsion_names[name]][0])

        for name in range(len(self.systems_names)):
            weight_C.append(inputs['weight_systems:' + self.systems_names[name]][0])

        for name in range(len(self.furniture_names)):
            weight_D.append(inputs['weight_furniture:' + self.furniture_names[name]][0])

        # Crew
        E = inputs['weight_crew:E'][0]

        A = sum(weight_A)
        B = sum(weight_B)
        C = sum(weight_C)
        D = sum(weight_D)

        oew = A + B + C + D + E

        outputs['weight_airframe:A'] = A
        outputs['weight_propulsion:B'] = B
        outputs['weight_systems:C'] = C
        outputs['weight_furniture:D'] = D
        outputs['weight:OEW'] = oew
