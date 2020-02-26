"""
    Estimation of other components center of gravities
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
from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeOthersCG(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Other components center of gravities estimation """

    def setup(self):

        self.add_input('geometry:wing:root:leading_edge:x', val=np.nan, units='m')
        self.add_input('geometry:wing:MAC:length', val=np.nan, units='m')
        self.add_input('geometry:wing:root:chord', val=np.nan, units='m')
        self.add_input('geometry:fuselage:length', val=np.nan, units='m')
        self.add_input('geometry:wing:MAC:x', val=np.nan, units='m')
        self.add_input('geometry:fuselage:front_length', val=np.nan, units='m')
        self.add_input('geometry:fuselage:rear_length', val=np.nan, units='m')
        self.add_input('weight:propulsion:engine:CG:x', val=np.nan, units='m')
        self.add_input('weight:furniture:passenger_seats:CG:x', val=np.nan, units='m')
        self.add_input('weight:propulsion:engine:mass', val=np.nan, units='kg')
        self.add_input('geometry:cabin:NPAX1', val=np.nan)
        self.add_input('geometry:cabin:seats:economical:count_by_row', val=np.nan)
        self.add_input('geometry:cabin:seats:economical:length', val=np.nan, units='m')

        # TODO: add description of these CGs
        self.add_output('weight:airframe:fuselage:CG:x', units='m')
        self.add_output('weight:airframe:landing_gear:front:CG:x', units='m')
        self.add_output('weight:airframe:pylon:CG:x', units='m')
        self.add_output('weight:airframe:paint:CG:x', units='m')
        self.add_output('weight:propulsion:fuel_lines:CG:x', units='m')
        self.add_output('weight:propulsion:unconsumables:CG:x', units='m')
        self.add_output('weight:systems:power:auxiliary_power_unit:CG:x', units='m')
        self.add_output('weight:systems:power:electric_systems:CG:x', units='m')
        self.add_output('weight:systems:power:hydraulic_systems:CG:x', units='m')
        self.add_output('weight:systems:life_support:insulation:CG:x', units='m')
        self.add_output('weight:systems:life_support:air_conditioning:CG:x', units='m')
        self.add_output('weight:systems:life_support:de-icing:CG:x', units='m')
        self.add_output('weight:systems:life_support:cabin_lighting:CG:x', units='m')
        self.add_output('weight:systems:life_support:seats_crew_accommodation:CG:x', units='m')
        self.add_output('weight:systems:life_support:oxygen:CG:x', units='m')
        self.add_output('weight:systems:life_support:safety_equipment:CG:x', units='m')
        self.add_output('weight:systems:navigation:CG:x', units='m')
        self.add_output('weight:systems:transmission:CG:x', units='m')
        self.add_output('weight:systems:operational:radar:CG:x', units='m')
        self.add_output('weight:systems:operational:cargo_hold:CG:x', units='m')
        self.add_output('weight:furniture:cargo_configuration:CG:x', units='m')
        self.add_output('weight:furniture:food_water:CG:x', units='m')
        self.add_output('weight:furniture:security_kit:CG:x', units='m')
        self.add_output('weight:furniture:toilets:CG:x', units='m')
        self.add_output('weight:payload:PAX:CG:x', units='m')
        self.add_output('weight:payload:rear_fret:CG:x', units='m')
        self.add_output('weight:payload:front_fret:CG:x', units='m')

        self.declare_partials(
            'weight:airframe:fuselage:CG:x', 'geometry:fuselage:length', method='fd')
        self.declare_partials(
            'weight:airframe:landing_gear:front:CG:x', 'geometry:fuselage:front_length',
            method='fd')
        self.declare_partials(
            'weight:airframe:pylon:CG:x', 'weight:propulsion:engine:CG:x', method='fd')
        self.declare_partials('weight:propulsion:fuel_lines:CG:x',
                              'weight:propulsion:engine:CG:x', method='fd')
        self.declare_partials('weight:propulsion:unconsumables:CG:x',
                              'weight:propulsion:engine:CG:x', method='fd')
        self.declare_partials(['weight:systems:power:auxiliary_power_unit:CG:x',
                               'weight:systems:power:electric_systems:CG:x',
                               'weight:systems:power:hydraulic_systems:CG:x',
                               'weight:systems:life_support:insulation:CG:x',
                               'weight:systems:life_support:cabin_lighting:CG:x',
                               'weight:systems:transmission:CG:x',
                               'weight:systems:operational:radar:CG:x'], 'geometry:fuselage:length',
                              method='fd')
        self.declare_partials(['weight:systems:life_support:air_conditioning:CG:x',
                               'weight:systems:life_support:seats_crew_accommodation:CG:x',
                               'weight:systems:life_support:oxygen:CG:x',
                               'weight:systems:operational:cargo_hold:CG:x'],
                              'weight:furniture:passenger_seats:CG:x', method='fd')
        self.declare_partials('weight:systems:life_support:de-icing:CG:x', [
            'geometry:wing:MAC:x', 'geometry:wing:MAC:length'], method='fd')
        self.declare_partials('weight:systems:life_support:safety_equipment:CG:x',
                              ['weight:propulsion:engine:mass', 'weight:propulsion:engine:CG:x',
                               'geometry:cabin:NPAX1', 'weight:furniture:passenger_seats:CG:x'], method='fd')
        self.declare_partials(
            'weight:systems:navigation:CG:x', 'geometry:fuselage:front_length', method='fd')
        self.declare_partials('weight:furniture:food_water:CG:x',
                              ['geometry:fuselage:length', 'geometry:fuselage:rear_length',
                               'geometry:cabin:seats:economical:length',
                               'geometry:cabin:seats:economical:count_by_row'], method='fd')
        self.declare_partials(
            ['weight:furniture:security_kit:CG:x', 'weight:furniture:toilets:CG:x'], 'weight:furniture:passenger_seats:CG:x', method='fd')
        self.declare_partials(
            'weight:payload:PAX:CG:x', 'weight:furniture:passenger_seats:CG:x', method='fd')
        self.declare_partials('weight:payload:rear_fret:CG:x',
                              ['geometry:fuselage:rear_length', 'geometry:wing:MAC:length',
                               'geometry:wing:root:leading_edge:x',
                               'geometry:wing:root:chord',
                               'geometry:cabin:seats:economical:count_by_row',
                               'geometry:cabin:seats:economical:length',
                               'geometry:wing:MAC:x', 'geometry:fuselage:length'],
                              method='fd')
        self.declare_partials('weight:payload:front_fret:CG:x',
                              ['geometry:fuselage:front_length', 'geometry:wing:MAC:length',
                               'geometry:wing:root:leading_edge:x', 'geometry:wing:MAC:x'],
                              method='fd')

    def compute(self, inputs, outputs):
        x0_wing = inputs['geometry:wing:root:leading_edge:x']
        l0_wing = inputs['geometry:wing:MAC:length']
        l2_wing = inputs['geometry:wing:root:chord']
        fus_length = inputs['geometry:fuselage:length']
        fa_length = inputs['geometry:wing:MAC:x']
        lav = inputs['geometry:fuselage:front_length']
        lar = inputs['geometry:fuselage:rear_length']
        x_cg_b1 = inputs['weight:propulsion:engine:CG:x']
        x_cg_d2 = inputs['weight:furniture:passenger_seats:CG:x']
        weight_engines = inputs['weight:propulsion:engine:mass']
        npax1 = inputs['geometry:cabin:NPAX1']
        front_seat_number_eco = inputs['geometry:cabin:seats:economical:count_by_row']
        ls_eco = inputs['geometry:cabin:seats:economical:length']

        x_cg_a2 = 0.45 * fus_length

        # Assume cg of nose landing gear is at 75% of lav
        x_cg_a52 = lav * 0.75
        x_cg_a6 = x_cg_b1
        x_cg_b2 = x_cg_b1
        x_cg_b3 = x_cg_b1

        # APU is installed after the pressure bulkhead, and pressurized area is
        # about 80% of fuselage length
        x_cg_c11 = 0.95 * fus_length
        x_cg_c12 = 0.5 * fus_length
        x_cg_c13 = 0.5 * fus_length
        x_cg_c21 = 0.45 * fus_length
        x_cg_c22 = x_cg_d2
        x_cg_c23 = fa_length - 0.15 * l0_wing
        x_cg_c24 = 0.45 * fus_length
        x_cg_c25 = x_cg_d2
        x_cg_c26 = x_cg_d2
        x_cg_c27 = (0.01 * weight_engines *
                    x_cg_b1 +
                    2.3 * npax1 *
                    x_cg_d2) / (
                           0.01 * weight_engines +
                           2.3 * npax1)
        x_cg_c3 = lav * 0.8
        x_cg_c4 = 0.5 * fus_length
        x_cg_c51 = 0.02 * fus_length
        x_cg_c52 = x_cg_d2

        x_cg_d3 = lav + (fus_length - lav - lar) + ls_eco * \
                  front_seat_number_eco + 0.92 + 0.432
        x_cg_d5 = x_cg_d2

        length_front_fret = (fa_length - 0.25 * l0_wing - x0_wing - lav)
        x_cg_front_fret = lav + length_front_fret * 0.5

        length_rear_fret = fus_length - lar + (
                front_seat_number_eco - 5) * \
                           ls_eco - (lav + length_front_fret + 0.8 * l2_wing)

        x_cg_rear_fret = lav + length_front_fret + \
                         0.8 * l2_wing + length_rear_fret * 0.5

        x_cg_pl = x_cg_d2

        outputs['weight:airframe:fuselage:CG:x'] = x_cg_a2
        outputs['weight:airframe:landing_gear:front:CG:x'] = x_cg_a52
        outputs['weight:airframe:pylon:CG:x'] = x_cg_a6
        outputs['weight:airframe:paint:CG:x'] = 0.

        outputs['weight:propulsion:fuel_lines:CG:x'] = x_cg_b2
        outputs['weight:propulsion:unconsumables:CG:x'] = x_cg_b3

        outputs['weight:systems:power:auxiliary_power_unit:CG:x'] = x_cg_c11
        outputs['weight:systems:power:electric_systems:CG:x'] = x_cg_c12
        outputs['weight:systems:power:hydraulic_systems:CG:x'] = x_cg_c13
        outputs['weight:systems:life_support:insulation:CG:x'] = x_cg_c21
        outputs['weight:systems:life_support:air_conditioning:CG:x'] = x_cg_c22
        outputs['weight:systems:life_support:de-icing:CG:x'] = x_cg_c23
        outputs['weight:systems:life_support:cabin_lighting:CG:x'] = x_cg_c24
        outputs['weight:systems:life_support:seats_crew_accommodation:CG:x'] = x_cg_c25
        outputs['weight:systems:life_support:oxygen:CG:x'] = x_cg_c26
        outputs['weight:systems:life_support:safety_equipment:CG:x'] = x_cg_c27
        outputs['weight:systems:navigation:CG:x'] = x_cg_c3
        outputs['weight:systems:transmission:CG:x'] = x_cg_c4
        outputs['weight:systems:operational:radar:CG:x'] = x_cg_c51
        outputs['weight:systems:operational:cargo_hold:CG:x'] = x_cg_c52

        outputs['weight:furniture:cargo_configuration:CG:x'] = 0.
        outputs['weight:furniture:food_water:CG:x'] = x_cg_d3
        outputs['weight:furniture:security_kit:CG:x'] = x_cg_d5
        outputs['weight:furniture:toilets:CG:x'] = x_cg_d5
        outputs['weight:payload:PAX:CG:x'] = x_cg_pl
        outputs['weight:payload:rear_fret:CG:x'] = x_cg_rear_fret
        outputs['weight:payload:front_fret:CG:x'] = x_cg_front_fret
