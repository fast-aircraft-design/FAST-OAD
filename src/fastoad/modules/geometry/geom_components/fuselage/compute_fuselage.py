"""
    Estimation of geometry of fuselase part A - Cabin (Commercial)
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
from math import sqrt

import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeFuselageGeometryBasic(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Geometry of fuselage part A - Cabin (Commercial) estimation """

    def setup(self):

        self.add_input('geometry:cabin:NPAX1', val=np.nan)
        self.add_input('geometry:fuselage:length', val=np.nan, units='m')
        self.add_input('geometry:fuselage:maximum_width', val=np.nan, units='m')
        self.add_input('geometry:fuselage:maximum_height', val=np.nan, units='m')
        self.add_input('geometry:fuselage:front_length', val=np.nan, units='m')
        self.add_input('geometry:fuselage:rear_length', val=np.nan, units='m')
        self.add_input('geometry:fuselage:PAX_length', val=np.nan, units='m')

        self.add_output('cg_pl:CG_PAX', units='m')
        self.add_output('weight:systems:flight_kit:CG:x', units='m')
        self.add_output('weight:furniture:passenger_seats:CG:x', units='m')
        self.add_output('geometry:cabin:length', units='m')
        self.add_output('geometry:fuselage:wetted_area', units='m**2')
        self.add_output('geometry:cabin:crew_count:commercial')

        self.declare_partials('cg_pl:CG_PAX',
                              ['geometry:fuselage:front_length', 'geometry:fuselage:PAX_length'],
                              method='fd')
        self.declare_partials('weight:systems:flight_kit:CG:x',
                              ['geometry:fuselage:front_length', 'geometry:fuselage:PAX_length'],
                              method='fd')
        self.declare_partials('weight:furniture:passenger_seats:CG:x',
                              ['geometry:fuselage:front_length', 'geometry:fuselage:PAX_length'],
                              method='fd')
        self.declare_partials('geometry:cabin:length',
                              ['geometry:fuselage:length'], method='fd')
        self.declare_partials('geometry:fuselage:wetted_area',
                              ['geometry:fuselage:maximum_width',
                               'geometry:fuselage:maximum_height',
                               'geometry:fuselage:front_length', 'geometry:fuselage:rear_length',
                               'geometry:fuselage:length'], method='fd')
        self.declare_partials('geometry:cabin:crew_count:commercial',
                              ['geometry:cabin:NPAX1'], method='fd')

    def compute(self, inputs, outputs):
        npax_1 = inputs['geometry:cabin:NPAX1']
        fus_length = inputs['geometry:fuselage:length']
        b_f = inputs['geometry:fuselage:maximum_width']
        h_f = inputs['geometry:fuselage:maximum_height']
        lav = inputs['geometry:fuselage:front_length']
        lar = inputs['geometry:fuselage:rear_length']
        lpax = inputs['geometry:fuselage:PAX_length']

        l_cyl = fus_length - lav - lar
        cabin_length = 0.81 * fus_length
        x_cg_passenger = lav + lpax / 2.0
        x_cg_d2 = lav + 0.35 * lpax
        x_cg_c6 = lav + 0.1 * lpax
        pnc = int((npax_1 + 17) / 35)

        # Equivalent diameter of the fuselage
        fus_dia = sqrt(b_f * h_f)
        wet_area_nose = 2.45 * fus_dia * lav
        wet_area_cyl = 3.1416 * fus_dia * l_cyl
        wet_area_tail = 2.3 * fus_dia * lar
        wet_area_fus = (wet_area_nose + wet_area_cyl + wet_area_tail)

        outputs['cg_pl:CG_PAX'] = x_cg_passenger
        outputs['weight:systems:flight_kit:CG:x'] = x_cg_c6
        outputs['weight:furniture:passenger_seats:CG:x'] = x_cg_d2
        outputs['geometry:cabin:length'] = cabin_length
        outputs['geometry:cabin:crew_count:commercial'] = pnc
        outputs['geometry:fuselage:wetted_area'] = wet_area_fus


class ComputeFuselageGeometryCabinSizing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Geometry of fuselage part A - Cabin (Commercial) estimation """

    def setup(self):

        self.add_input('geometry:cabin:seats:economical:width', val=np.nan, units='m')
        self.add_input('geometry:cabin:seats:economical:length', val=np.nan, units='m')
        self.add_input('geometry:cabin:seats:economical:count_by_row', val=np.nan)
        self.add_input('geometry:cabin:aisle_width', val=np.nan, units='m')
        self.add_input('geometry:cabin:exit_width', val=np.nan, units='m')
        self.add_input('TLAR:NPAX', val=np.nan)
        self.add_input('geometry:propulsion:engine:count', val=np.nan)

        self.add_output('geometry:cabin:NPAX1')
        self.add_output('geometry:cabin:seat_rows:count')
        self.add_output('weight:systems:flight_kit:CG:x', units='m')
        self.add_output('weight:furniture:passenger_seats:CG:x', units='m')
        self.add_output('geometry:fuselage:length', units='m')
        self.add_output('geometry:fuselage:maximum_width', units='m')
        self.add_output('geometry:fuselage:maximum_height', units='m')
        self.add_output('geometry:fuselage:front_length', units='m')
        self.add_output('geometry:fuselage:rear_length', units='m')
        self.add_output('geometry:fuselage:PAX_length', units='m')
        self.add_output('geometry:cabin:length', units='m')
        self.add_output('geometry:fuselage:wetted_area', units='m**2')
        self.add_output('geometry:cabin:crew_count:commercial')

        self.declare_partials('geometry:cabin:NPAX1', ['TLAR:NPAX'], method='fd')
        self.declare_partials('geometry:cabin:seat_rows:count',
                              ['geometry:cabin:seats:economical:count_by_row', 'TLAR:NPAX'],
                              method='fd')
        self.declare_partials('geometry:fuselage:maximum_width',
                              ['geometry:cabin:seats:economical:count_by_row',
                               'geometry:cabin:seats:economical:width',
                               'geometry:cabin:aisle_width'], method='fd')
        self.declare_partials('geometry:fuselage:maximum_height',
                              ['geometry:cabin:seats:economical:count_by_row',
                               'geometry:cabin:seats:economical:width',
                               'geometry:cabin:aisle_width'], method='fd')
        self.declare_partials('geometry:fuselage:front_length',
                              ['geometry:cabin:seats:economical:count_by_row',
                               'geometry:cabin:seats:economical:width',
                               'geometry:cabin:aisle_width'], method='fd')
        self.declare_partials('geometry:fuselage:rear_length',
                              ['geometry:cabin:seats:economical:count_by_row',
                               'geometry:cabin:seats:economical:width',
                               'geometry:cabin:aisle_width'], method='fd')
        self.declare_partials('geometry:fuselage:PAX_length', [
            'geometry:cabin:seats:economical:length', 'geometry:cabin:exit_width'], method='fd')
        self.declare_partials('geometry:fuselage:length',
                              ['geometry:cabin:seats:economical:count_by_row',
                               'geometry:cabin:aisle_width',
                               'geometry:cabin:seats:economical:length',
                               'geometry:cabin:seats:economical:width',
                               'geometry:cabin:exit_width'], method='fd')
        self.declare_partials('geometry:cabin:length',
                              ['geometry:cabin:seats:economical:count_by_row',
                               'geometry:cabin:aisle_width',
                               'geometry:cabin:seats:economical:length',
                               'geometry:cabin:seats:economical:width',
                               'geometry:cabin:exit_width'], method='fd')
        self.declare_partials('weight:systems:flight_kit:CG:x',
                              ['geometry:cabin:seats:economical:count_by_row',
                               'geometry:cabin:seats:economical:width',
                               'geometry:cabin:seats:economical:length',
                               'geometry:cabin:exit_width', 'geometry:cabin:aisle_width'],
                              method='fd')
        self.declare_partials('weight:furniture:passenger_seats:CG:x',
                              ['geometry:cabin:seats:economical:count_by_row', 'geometry:cabin:seats:economical:width',
                               'geometry:cabin:seats:economical:length', 'geometry:cabin:exit_width', 'geometry:cabin:aisle_width'], method='fd')
        self.declare_partials('geometry:fuselage:wetted_area',
                              ['geometry:cabin:seats:economical:count_by_row',
                               'geometry:cabin:aisle_width',
                               'geometry:cabin:seats:economical:length',
                               'geometry:cabin:seats:economical:width',
                               'geometry:cabin:exit_width'], method='fd')

    def compute(self, inputs, outputs):
        front_seat_number_eco = inputs['geometry:cabin:seats:economical:count_by_row']
        ws_eco = inputs['geometry:cabin:seats:economical:width']
        ls_eco = inputs['geometry:cabin:seats:economical:length']
        w_aisle = inputs['geometry:cabin:aisle_width']
        w_exit = inputs['geometry:cabin:exit_width']
        npax = inputs['TLAR:NPAX']
        n_engines = inputs['geometry:propulsion:engine:count']

        # Cabin width = N * seat width + Aisle width + (N+2)*2"+2 * 1"
        wcabin = front_seat_number_eco * ws_eco + \
            w_aisle + (front_seat_number_eco + 2) * 0.051 + 0.05

        # Number of rows = Npax / N
        npax_1 = int(1.05 * npax)
        n_rows = int(npax_1 / front_seat_number_eco)
        pnc = int((npax+17)/35)
        # Length of pax cabin = Length of seat area + Width of 1 Emergency
        # exits
        lpax = (n_rows * ls_eco) + 1 * w_exit
        l_cyl = lpax - (2 * front_seat_number_eco - 4) * ls_eco
        r_i = wcabin / 2
        radius = 1.06 * r_i
        # Cylindrical fuselage
        b_f = 2 * radius
        # 0.14m is the distance between both lobe centers of the fuselage
        h_f = b_f + 0.14
        lav = 1.7 * h_f

        if n_engines == 3.0:
            lar = 3.0 * h_f
        else:
            lar = 3.60 * h_f

        fus_length = lav + lar + l_cyl
        cabin_length = 0.81 * fus_length
        x_cg_c6 = lav - (front_seat_number_eco - 4) * ls_eco + lpax * 0.1
        x_cg_d2 = lav - (front_seat_number_eco - 4) * ls_eco + lpax / 2

        # Equivalent diameter of the fuselage
        fus_dia = sqrt(b_f * h_f)
        wet_area_nose = 2.45 * fus_dia * lav
        wet_area_cyl = 3.1416 * fus_dia * l_cyl
        wet_area_tail = 2.3 * fus_dia * lar
        wet_area_fus = (wet_area_nose + wet_area_cyl + wet_area_tail)

        outputs['geometry:cabin:seat_rows:count'] = n_rows
        outputs['geometry:cabin:NPAX1'] = npax_1
        outputs['weight:systems:flight_kit:CG:x'] = x_cg_c6
        outputs['weight:furniture:passenger_seats:CG:x'] = x_cg_d2
        outputs['geometry:fuselage:length'] = fus_length
        outputs['geometry:fuselage:maximum_width'] = b_f
        outputs['geometry:fuselage:maximum_height'] = h_f
        outputs['geometry:fuselage:front_length'] = lav
        outputs['geometry:fuselage:rear_length'] = lar
        outputs['geometry:fuselage:PAX_length'] = lpax
        outputs['geometry:cabin:length'] = cabin_length
        outputs['geometry:cabin:crew_count:commercial'] = pnc
        outputs['geometry:fuselage:wetted_area'] = wet_area_fus
