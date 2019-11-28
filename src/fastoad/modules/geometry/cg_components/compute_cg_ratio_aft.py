"""
    Estimation of center of gravity ratio with aft
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
from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeCGratioAft(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Center of gravity ratio with aft estimation """

    def initialize(self):

        # TODO: make this more generic
        airframe_names = ['A1', 'A2', 'A31', 'A32', 'A4', 'A51', 'A52', 'A6', 'A7']
        propulsion_names = ['B1', 'B2', 'B3']
        systems_names = ['C11', 'C12', 'C13', 'C21', 'C22', 'C23', 'C24', 'C25',
                            'C26', 'C27', 'C3', 'C4', 'C51', 'C52', 'C6']
        furniture_names = ['D1', 'D2', 'D3', 'D4', 'D5']

        self.options.declare('airframe_names', default=airframe_names)
        self.options.declare('propulsion_names', default=propulsion_names)
        self.options.declare('systems_names', default=systems_names)
        self.options.declare('furniture_names', default=furniture_names)

        self.airframe_names = self.options['airframe_names']
        self.propulsion_names = self.options['propulsion_names']
        self.systems_names = self.options['systems_names']
        self.furniture_names = self.options['furniture_names']

    def setup(self):

        for name in range(len(self.airframe_names)):
            self.add_input('cg_airframe:'+self.airframe_names[name], val=np.nan, units='m')
            self.add_input('weight_airframe:'+self.airframe_names[name], val=np.nan, units='kg')
            self.declare_partials('x_cg_plane_up', ['weight_airframe:'+self.airframe_names[name],
                                   'cg_airframe:'+self.airframe_names[name]], method='fd')
            self.declare_partials('x_cg_plane_down', 'weight_airframe:'+self.airframe_names[name],
                                  method='fd')
        for name in range(len(self.propulsion_names)):
            self.add_input('cg_propulsion:'+self.propulsion_names[name], val=np.nan, units='m')
            self.add_input('weight_propulsion:'+self.propulsion_names[name], val=np.nan, units='kg')
            self.declare_partials('x_cg_plane_up',
                                  ['weight_propulsion:'+self.propulsion_names[name],
                                   'cg_propulsion:'+self.propulsion_names[name]],
                                   method='fd')
            self.declare_partials('x_cg_plane_down',
                                  'weight_propulsion:'+self.propulsion_names[name],
                                  method='fd')
        for name in range(len(self.systems_names)):
            self.add_input('cg_systems:'+self.systems_names[name], val=np.nan, units='m')
            self.add_input('weight_systems:'+self.systems_names[name], val=np.nan, units='kg')
            self.declare_partials('x_cg_plane_up', ['weight_systems:'+self.systems_names[name],
                                   'cg_systems:'+self.systems_names[name]], method='fd')
            self.declare_partials('x_cg_plane_down', 'weight_systems:'+self.systems_names[name],
                                  method='fd')
        for name in range(len(self.furniture_names)):
            self.add_input('cg_furniture:'+self.furniture_names[name], val=np.nan, units='m')
            self.add_input('weight_furniture:'+self.furniture_names[name], val=np.nan, units='kg')
            self.declare_partials('x_cg_plane_up', ['weight_furniture:'+self.furniture_names[name],
                                   'cg_furniture:'+self.furniture_names[name]], method='fd')
            self.declare_partials('x_cg_plane_down', 'weight_furniture:'+self.furniture_names[name],
                                  method='fd')


        self.add_input('geometry:wing_l0', val=np.nan, units='m')
        self.add_input('geometry:wing_position', val=np.nan, units='m')

        self.add_output('x_cg_plane_up')
        self.add_output('x_cg_plane_down')
        self.add_output('cg_ratio_aft')

        self.declare_partials('cg_ratio_aft', '*', method='fd')


    def compute(self, inputs, outputs):
        l0_wing = inputs['geometry:wing_l0']
        fa_length = inputs['geometry:wing_position']

        weight_all = []
        cg_all = []

        for name in range(len(self.airframe_names)):
            weight_all.append(inputs['weight_airframe:'+self.airframe_names[name]])
            cg_all.append(inputs['cg_airframe:'+self.airframe_names[name]])

        for name in range(len(self.propulsion_names)):
            weight_all.append(inputs['weight_propulsion:'+self.propulsion_names[name]])
            cg_all.append(inputs['cg_propulsion:'+self.propulsion_names[name]])

        for name in range(len(self.systems_names)):
            weight_all.append(inputs['weight_systems:'+self.systems_names[name]])
            cg_all.append(inputs['cg_systems:'+self.systems_names[name]])

        for name in range(len(self.furniture_names)):
            weight_all.append(inputs['weight_furniture:'+self.furniture_names[name]])
            cg_all.append(inputs['cg_furniture:'+self.furniture_names[name]])

        x_cg_plane_up = 0
        x_cg_plane_down = 0
        for i, weight in enumerate(weight_all):
            x_cg_plane_up += weight * cg_all[i]
            x_cg_plane_down += weight
        # afterward,no fuel, no payload
        x_cg_plane_aft = x_cg_plane_up / x_cg_plane_down
        cg_ratio_aft = (x_cg_plane_aft - fa_length + 0.25 * l0_wing) / l0_wing

        outputs['x_cg_plane_up'] = x_cg_plane_up
        outputs['x_cg_plane_down'] = x_cg_plane_down
        outputs['cg_ratio_aft'] = cg_ratio_aft
