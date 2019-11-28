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
import openmdao.api as om


class ComputeCGRatioAft(om.Group):

    def setup(self):
        self.add_subsystem('cg_all', ComputeCG(), promotes=['*'])
        self.add_subsystem('cg_ratio', CGRatio(), promotes=['*'])


class ComputeCG(om.ExplicitComponent):

    def initialize(self):
        self.options.declare('cg_names', default=['cg_airframe:A1',
                                                  'cg_airframe:A2',
                                                  'cg_airframe:A31',
                                                  'cg_airframe:A32',
                                                  'cg_airframe:A4',
                                                  'cg_airframe:A51',
                                                  'cg_airframe:A52',
                                                  'cg_airframe:A6',
                                                  'cg_airframe:A7',
                                                  'cg_propulsion:B1',
                                                  'cg_propulsion:B2',
                                                  'cg_propulsion:B3',
                                                  'cg_systems:C11',
                                                  'cg_systems:C12',
                                                  'cg_systems:C13',
                                                  'cg_systems:C21',
                                                  'cg_systems:C22',
                                                  'cg_systems:C23',
                                                  'cg_systems:C24',
                                                  'cg_systems:C25',
                                                  'cg_systems:C26',
                                                  'cg_systems:C27',
                                                  'cg_systems:C3',
                                                  'cg_systems:C4',
                                                  'cg_systems:C51',
                                                  'cg_systems:C52',
                                                  'cg_systems:C6',
                                                  'cg_furniture:D1',
                                                  'cg_furniture:D2',
                                                  'cg_furniture:D3',
                                                  'cg_furniture:D4',
                                                  'cg_furniture:D5'
                                                  ])

        self.options.declare('mass_names', ['weight_airframe:A1',
                                            'weight_airframe:A2',
                                            'weight_airframe:A31',
                                            'weight_airframe:A32',
                                            'weight_airframe:A4',
                                            'weight_airframe:A51',
                                            'weight_airframe:A52',
                                            'weight_airframe:A6',
                                            'weight_airframe:A7',
                                            'weight_propulsion:B1',
                                            'weight_propulsion:B2',
                                            'weight_propulsion:B3',
                                            'weight_systems:C11',
                                            'weight_systems:C12',
                                            'weight_systems:C13',
                                            'weight_systems:C21',
                                            'weight_systems:C22',
                                            'weight_systems:C23',
                                            'weight_systems:C24',
                                            'weight_systems:C25',
                                            'weight_systems:C26',
                                            'weight_systems:C27',
                                            'weight_systems:C3',
                                            'weight_systems:C4',
                                            'weight_systems:C51',
                                            'weight_systems:C52',
                                            'weight_systems:C6',
                                            'weight_furniture:D1',
                                            'weight_furniture:D2',
                                            'weight_furniture:D3',
                                            'weight_furniture:D4',
                                            'weight_furniture:D5',
                                            ])

    def setup(self):
        for cg_name in self.options['cg_names']:
            self.add_input(cg_name, val=np.nan, units='m')
        for mass_name in self.options['mass_names']:
            self.add_input(mass_name, val=np.nan, units='kg')

        self.add_output('x_cg_plane_up', units='m')
        self.add_output('x_cg_plane_down', units='m')
        self.add_output('x_cg_plane_aft', units='m')

        self.declare_partials('x_cg_plane_up', '*', method='fd')
        self.declare_partials('x_cg_plane_down', '*', method='fd')
        self.declare_partials('x_cg_plane_aft', '*', method='fd')

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        cgs = [inputs[cg_name][0] for cg_name in self.options['cg_names']]
        masses = [inputs[mass_name][0] for mass_name in self.options['mass_names']]

        outputs['x_cg_plane_up'] = np.dot(cgs, masses)
        outputs['x_cg_plane_down'] = np.sum(masses)
        outputs['x_cg_plane_aft'] = outputs['x_cg_plane_up'] / outputs['x_cg_plane_down']


class CGRatio(om.ExplicitComponent):
    def setup(self):
        self.add_input('x_cg_plane_aft', val=np.nan, units='m')
        self.add_input('geometry:wing_l0', val=np.nan, units='m')
        self.add_input('geometry:wing_position', val=np.nan, units='m')

        self.add_output('cg_ratio_aft')

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        x_cg_all = inputs['x_cg_plane_aft']
        wing_position = inputs['geometry:wing_position']
        mac = inputs['geometry:wing_l0']

        outputs['cg_ratio_aft'] = (x_cg_all - wing_position + 0.25 * mac) / mac
