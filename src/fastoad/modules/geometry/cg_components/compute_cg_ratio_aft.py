"""
    Estimation of center of gravity ratio with aft
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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
        self.options.declare('cg_names', default=['weight:airframe:wing:CG:x',
                                                  'weight:airframe:fuselage:CG:x',
                                                  'weight:airframe:horizontal_tail:CG:x',
                                                  'weight:airframe:vertical_tail:CG:x',
                                                  'weight:airframe:flight_controls:CG:x',
                                                  'weight:airframe:landing_gear:main:CG:x',
                                                  'weight:airframe:landing_gear:front:CG:x',
                                                  'weight:airframe:pylon:CG:x',
                                                  'weight:airframe:paint:CG:x',
                                                  'weight:propulsion:engine:CG:x',
                                                  'weight:propulsion:fuel_lines:CG:x',
                                                  'weight:propulsion:unconsumables:CG:x',
                                                  'weight:systems:power:auxiliary_power_unit:CG:x',
                                                  'weight:systems:power:electric_systems:CG:x',
                                                  'weight:systems:power:hydraulic_systems:CG:x',
                                                  'weight:systems:life_support:insulation:CG:x',
                                                  'weight:systems:life_support:air_conditioning:CG:x',
                                                  'weight:systems:life_support:de-icing:CG:x',
                                                  'weight:systems:life_support:cabin_lighting:CG:x',
                                                  'weight:systems:life_support:seats_crew_accommodation:CG:x',
                                                  'weight:systems:life_support:oxygen:CG:x',
                                                  'weight:systems:life_support:safety_equipment:CG:x',
                                                  'weight:systems:navigation:CG:x',
                                                  'weight:systems:transmission:CG:x',
                                                  'weight:systems:operational:radar:CG:x',
                                                  'weight:systems:operational:cargo_hold:CG:x',
                                                  'weight:systems:flight_kit:CG:x',
                                                  'weight:furniture:cargo_configuration:CG:x',
                                                  'weight:furniture:passenger_seats:CG:x',
                                                  'weight:furniture:food_water:CG:x',
                                                  'weight:furniture:security_kit:CG:x',
                                                  'weight:furniture:toilets:CG:x'
                                                  ])

        self.options.declare('mass_names', ['weight:airframe:wing:mass',
                                            'weight:airframe:fuselage:mass',
                                            'weight:airframe:horizontal_tail:mass',
                                            'weight:airframe:vertical_tail:mass',
                                            'weight:airframe:flight_controls:mass',
                                            'weight:airframe:landing_gear:main:mass',
                                            'weight:airframe:landing_gear:front:mass',
                                            'weight:airframe:pylon:mass',
                                            'weight:airframe:paint:mass',
                                            'weight:propulsion:engine:mass',
                                            'weight:propulsion:fuel_lines:mass',
                                            'weight:propulsion:unconsumables:mass',
                                            'weight:systems:power:auxiliary_power_unit:mass',
                                            'weight:systems:power:electric_systems:mass',
                                            'weight:systems:power:hydraulic_systems:mass',
                                            'weight:systems:life_support:insulation:mass',
                                            'weight:systems:life_support:air_conditioning:mass',
                                            'weight:systems:life_support:de-icing:mass',
                                            'weight:systems:life_support:cabin_lighting:mass',
                                            'weight:systems:life_support:seats_crew_accommodation:mass',
                                            'weight:systems:life_support:oxygen:mass',
                                            'weight:systems:life_support:safety_equipment:mass',
                                            'weight:systems:navigation:mass',
                                            'weight:systems:transmission:mass',
                                            'weight:systems:operational:radar:mass',
                                            'weight:systems:operational:cargo_hold:mass',
                                            'weight:systems:flight_kit:mass',
                                            'weight:furniture:cargo_configuration:mass',
                                            'weight:furniture:passenger_seats:mass',
                                            'weight:furniture:food_water:mass',
                                            'weight:furniture:security_kit:mass',
                                            'weight:furniture:toilets:mass',
                                            ])

    def setup(self):
        for cg_name in self.options['cg_names']:
            self.add_input(cg_name, val=np.nan, units='m')
        for mass_name in self.options['mass_names']:
            self.add_input(mass_name, val=np.nan, units='kg')

        self.add_output('weight:aircraft_empty:mass', units='m')
        self.add_output('weight:aircraft_empty:CG:x', units='m')

        self.declare_partials('weight:aircraft_empty:mass', '*', method='fd')
        self.declare_partials('weight:aircraft_empty:CG:x', '*', method='fd')

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        cgs = [inputs[cg_name][0] for cg_name in self.options['cg_names']]
        masses = [inputs[mass_name][0] for mass_name in self.options['mass_names']]

        weight_moment = np.dot(cgs, masses)
        outputs['weight:aircraft_empty:mass'] = np.sum(masses)
        outputs['weight:aircraft_empty:CG:x'] = weight_moment / outputs[
            'weight:aircraft_empty:mass']


class CGRatio(om.ExplicitComponent):
    def setup(self):
        self.add_input('weight:aircraft_empty:CG:x', val=np.nan, units='m')
        self.add_input('geometry:wing:MAC:length', val=np.nan, units='m')
        self.add_input('geometry:wing:MAC:x', val=np.nan, units='m')

        self.add_output('weight:aircraft:empty:CG:ratio')

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        x_cg_all = inputs['weight:aircraft_empty:CG:x']
        wing_position = inputs['geometry:wing:MAC:x']
        mac = inputs['geometry:wing:MAC:length']

        outputs['weight:aircraft:empty:CG:ratio'] = (x_cg_all - wing_position + 0.25 * mac) / mac
