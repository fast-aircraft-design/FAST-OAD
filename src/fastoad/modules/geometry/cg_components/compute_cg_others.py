"""
    Estimation of other components center of gravities
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


class ComputeOthersCG(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Other components center of gravities estimation """

    def setup(self):

        self.add_input('geometry:wing_x0', val=np.nan, units='m')
        self.add_input('geometry:wing_l0', val=np.nan, units='m')
        self.add_input('geometry:wing_l2', val=np.nan, units='m')
        self.add_input('geometry:fuselage_length', val=np.nan, units='m')
        self.add_input('geometry:wing_position', val=np.nan, units='m')
        self.add_input('geometry:fuselage_LAV', val=np.nan, units='m')
        self.add_input('geometry:fuselage_LAR', val=np.nan, units='m')
        self.add_input('cg_propulsion:B1', val=np.nan, units='m')
        self.add_input('cg_furniture:D2', val=np.nan, units='m')
        self.add_input('weight_propulsion:B1', val=np.nan, units='kg')
        self.add_input('cabin:NPAX1', val=np.nan)
        self.add_input('cabin:front_seat_number_eco', val=np.nan)
        self.add_input('cabin:LSeco', val=np.nan, units='m')

        # TODO: add description of these CGs
        self.add_output('cg_airframe:A2', units='m')
        self.add_output('cg_airframe:A52', units='m')
        self.add_output('cg_airframe:A6', units='m')
        self.add_output('cg_airframe:A7', units='m')
        self.add_output('cg_propulsion:B2', units='m')
        self.add_output('cg_propulsion:B3', units='m')
        self.add_output('cg_systems:C11', units='m')
        self.add_output('cg_systems:C12', units='m')
        self.add_output('cg_systems:C13', units='m')
        self.add_output('cg_systems:C21', units='m')
        self.add_output('cg_systems:C22', units='m')
        self.add_output('cg_systems:C23', units='m')
        self.add_output('cg_systems:C24', units='m')
        self.add_output('cg_systems:C25', units='m')
        self.add_output('cg_systems:C26', units='m')
        self.add_output('cg_systems:C27', units='m')
        self.add_output('cg_systems:C3', units='m')
        self.add_output('cg_systems:C4', units='m')
        self.add_output('cg_systems:C51', units='m')
        self.add_output('cg_systems:C52', units='m')
        self.add_output('cg_furniture:D1', units='m')
        self.add_output('cg_furniture:D3', units='m')
        self.add_output('cg_furniture:D4', units='m')
        self.add_output('cg_furniture:D5', units='m')
        self.add_output('cg:cg_pax', units='m')
        self.add_output('cg:cg_rear_fret', units='m')
        self.add_output('cg:cg_front_fret', units='m')

        self.declare_partials(
            'cg_airframe:A2', 'geometry:fuselage_length', method='fd')
        self.declare_partials(
            'cg_airframe:A52', 'geometry:fuselage_LAV', method='fd')
        self.declare_partials(
            'cg_airframe:A6', 'cg_propulsion:B1', method='fd')
        self.declare_partials('cg_propulsion:B2',
                              'cg_propulsion:B1', method='fd')
        self.declare_partials('cg_propulsion:B3',
                              'cg_propulsion:B1', method='fd')
        self.declare_partials(['cg_systems:C11', 'cg_systems:C12', 'cg_systems:C13',
                               'cg_systems:C21', 'cg_systems:C24', 'cg_systems:C4',
                               'cg_systems:C51'], 'geometry:fuselage_length', method='fd')
        self.declare_partials(['cg_systems:C22', 'cg_systems:C25', 'cg_systems:C26',
                               'cg_systems:C52'], 'cg_furniture:D2', method='fd')
        self.declare_partials('cg_systems:C23', [
            'geometry:wing_position', 'geometry:wing_l0'], method='fd')
        self.declare_partials('cg_systems:C27',
                              ['weight_propulsion:B1', 'cg_propulsion:B1',
                               'cabin:NPAX1', 'cg_furniture:D2'], method='fd')
        self.declare_partials(
            'cg_systems:C3', 'geometry:fuselage_LAV', method='fd')
        self.declare_partials('cg_furniture:D3',
                              ['geometry:fuselage_length', 'geometry:fuselage_LAR',
                               'cabin:LSeco', 'cabin:front_seat_number_eco'], method='fd')
        self.declare_partials(
            ['cg_furniture:D4', 'cg_furniture:D5'], 'cg_furniture:D2', method='fd')
        self.declare_partials(
            'cg:cg_pax', 'cg_furniture:D2', method='fd')
        self.declare_partials('cg:cg_rear_fret',
                              ['geometry:fuselage_LAR', 'geometry:wing_l0', 'geometry:wing_x0',
                               'geometry:wing_l2', 'cabin:front_seat_number_eco', 'cabin:LSeco',
                               'geometry:wing_position', 'geometry:fuselage_length'],
                              method='fd')
        self.declare_partials('cg:cg_front_fret',
                              ['geometry:fuselage_LAV', 'geometry:wing_l0',
                               'geometry:wing_x0', 'geometry:wing_position'], method='fd')

    def compute(self, inputs, outputs):
        x0_wing = inputs['geometry:wing_x0']
        l0_wing = inputs['geometry:wing_l0']
        l2_wing = inputs['geometry:wing_l2']
        fus_length = inputs['geometry:fuselage_length']
        fa_length = inputs['geometry:wing_position']
        lav = inputs['geometry:fuselage_LAV']
        lar = inputs['geometry:fuselage_LAR']
        x_cg_b1 = inputs['cg_propulsion:B1']
        x_cg_d2 = inputs['cg_furniture:D2']
        weight_engines = inputs['weight_propulsion:B1']
        npax1 = inputs['cabin:NPAX1']
        front_seat_number_eco = inputs['cabin:front_seat_number_eco']
        ls_eco = inputs['cabin:LSeco']

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

        outputs['cg_airframe:A2'] = x_cg_a2
        outputs['cg_airframe:A52'] = x_cg_a52
        outputs['cg_airframe:A6'] = x_cg_a6
        outputs['cg_airframe:A7'] = 0.

        outputs['cg_propulsion:B2'] = x_cg_b2
        outputs['cg_propulsion:B3'] = x_cg_b3

        outputs['cg_systems:C11'] = x_cg_c11
        outputs['cg_systems:C12'] = x_cg_c12
        outputs['cg_systems:C13'] = x_cg_c13
        outputs['cg_systems:C21'] = x_cg_c21
        outputs['cg_systems:C22'] = x_cg_c22
        outputs['cg_systems:C23'] = x_cg_c23
        outputs['cg_systems:C24'] = x_cg_c24
        outputs['cg_systems:C25'] = x_cg_c25
        outputs['cg_systems:C26'] = x_cg_c26
        outputs['cg_systems:C27'] = x_cg_c27
        outputs['cg_systems:C3'] = x_cg_c3
        outputs['cg_systems:C4'] = x_cg_c4
        outputs['cg_systems:C51'] = x_cg_c51
        outputs['cg_systems:C52'] = x_cg_c52

        outputs['cg_furniture:D1'] = 0.
        outputs['cg_furniture:D3'] = x_cg_d3
        outputs['cg_furniture:D4'] = x_cg_d5
        outputs['cg_furniture:D5'] = x_cg_d5
        outputs['cg:cg_pax'] = x_cg_pl
        outputs['cg:cg_rear_fret'] = x_cg_rear_fret
        outputs['cg:cg_front_fret'] = x_cg_front_fret
