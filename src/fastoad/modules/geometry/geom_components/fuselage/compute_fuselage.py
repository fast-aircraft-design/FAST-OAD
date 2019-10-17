"""
    Estimation of geometry of fuselase part A - Cabin (Commercial)
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
from math import sqrt
import numpy as np

from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeFuselageGeometryBasic(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Geometry of fuselage part A - Cabin (Commercial) estimation """

    def setup(self):

        self.add_input('cabin:NPAX1', val=np.nan)
        self.add_input('geometry:fuselage_length', val=np.nan, units='m')
        self.add_input('geometry:fuselage_width_max', val=np.nan, units='m')
        self.add_input('geometry:fuselage_height_max', val=np.nan, units='m')
        self.add_input('geometry:fuselage_LAV', val=np.nan, units='m')
        self.add_input('geometry:fuselage_LAR', val=np.nan, units='m')
        self.add_input('geometry:fuselage_Lpax', val=np.nan, units='m')

        self.add_output('cg_pl:CG_PAX', units='m')
        self.add_output('cg_systems:C6', units='m')
        self.add_output('cg_furniture:D2', units='m')
        self.add_output('geometry:fuselage_Lcabin', units='m')
        self.add_output('geometry:fuselage_wet_area', units='m**2')
        self.add_output('cabin:PNC')

        self.declare_partials('cg_pl:CG_PAX',
                              ['geometry:fuselage_LAV', 'geometry:fuselage_Lpax'],
                              method='fd')
        self.declare_partials('cg_systems:C6',
                              ['geometry:fuselage_LAV', 'geometry:fuselage_Lpax'],
                              method='fd')
        self.declare_partials('cg_furniture:D2',
                              ['geometry:fuselage_LAV', 'geometry:fuselage_Lpax'],
                              method='fd')
        self.declare_partials('geometry:fuselage_Lcabin',
                              ['geometry:fuselage_length'], method='fd')
        self.declare_partials('geometry:fuselage_wet_area',
                              ['geometry:fuselage_width_max', 'geometry:fuselage_height_max',
                               'geometry:fuselage_LAV', 'geometry:fuselage_LAR',
                               'geometry:fuselage_length'], method='fd')
        self.declare_partials('cabin:PNC',
                              ['cabin:NPAX1'], method='fd')

    def compute(self, inputs, outputs):
        npax_1 = inputs['cabin:NPAX1']
        fus_length = inputs['geometry:fuselage_length']
        b_f = inputs['geometry:fuselage_width_max']
        h_f = inputs['geometry:fuselage_height_max']
        lav = inputs['geometry:fuselage_LAV']
        lar = inputs['geometry:fuselage_LAR']
        lpax = inputs['geometry:fuselage_Lpax']

        l_cyl = fus_length - lav - lar
        cabin_length = 0.81 * fus_length
        x_cg_passenger = lav + lpax/2.0
        x_cg_d2 = lav + 0.35*lpax
        x_cg_c6 = lav + 0.1*lpax
        pnc = int((npax_1+17)/35)

        # Equivalent diameter of the fuselage
        fus_dia = sqrt(b_f * h_f)
        wet_area_nose = 2.45 * fus_dia * lav
        wet_area_cyl = 3.1416 * fus_dia * l_cyl
        wet_area_tail = 2.3 * fus_dia * lar
        wet_area_fus = (wet_area_nose + wet_area_cyl + wet_area_tail)

        outputs['cg_pl:CG_PAX'] = x_cg_passenger
        outputs['cg_systems:C6'] = x_cg_c6
        outputs['cg_furniture:D2'] = x_cg_d2
        outputs['geometry:fuselage_Lcabin'] = cabin_length
        outputs['cabin:PNC'] = pnc
        outputs['geometry:fuselage_wet_area'] = wet_area_fus


class ComputeFuselageGeometryCabinSizing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Geometry of fuselage part A - Cabin (Commercial) estimation """

    def setup(self):

        self.add_input('cabin:WSeco', val=np.nan, units='inch')
        self.add_input('cabin:LSeco', val=np.nan, units='inch')
        self.add_input('cabin:front_seat_number_eco', val=np.nan)
        self.add_input('cabin:Waisle', val=np.nan, units='inch')
        self.add_input('cabin:Wexit', val=np.nan, units='inch')
        self.add_input('tlar:NPAX', val=np.nan)
        self.add_input('geometry:engine_number', val=np.nan)

        self.add_output('cabin:NPAX1')
        self.add_output('cabin:Nrows')
        self.add_output('cg_systems:C6', units='m')
        self.add_output('cg_furniture:D2', units='m')
        self.add_output('cg_pl:CG_PAX', units='m')
        self.add_output('geometry:fuselage_length', units='m')
        self.add_output('geometry:fuselage_width_max', units='m')
        self.add_output('geometry:fuselage_height_max', units='m')
        self.add_output('geometry:fuselage_LAV', units='m')
        self.add_output('geometry:fuselage_LAR', units='m')
        self.add_output('geometry:fuselage_Lpax', units='m')
        self.add_output('geometry:fuselage_Lcabin', units='m')
        self.add_output('geometry:fuselage_wet_area', units='m**2')
        self.add_output('cabin:PNC')

        self.declare_partials('cabin:NPAX1', ['tlar:NPAX'], method='fd')
        self.declare_partials('cabin:Nrows',
                              ['cabin:front_seat_number_eco', 'tlar:NPAX'],
                              method='fd')
        self.declare_partials('geometry:fuselage_width_max',
                              ['cabin:front_seat_number_eco', 'cabin:WSeco',
                               'cabin:Waisle'], method='fd')
        self.declare_partials('geometry:fuselage_height_max',
                              ['cabin:front_seat_number_eco', 'cabin:WSeco',
                               'cabin:Waisle'], method='fd')
        self.declare_partials('geometry:fuselage_LAV',
                              ['cabin:front_seat_number_eco', 'cabin:WSeco',
                               'cabin:Waisle'], method='fd')
        self.declare_partials('geometry:fuselage_LAR',
                              ['cabin:front_seat_number_eco', 'cabin:WSeco',
                               'cabin:Waisle'], method='fd')
        self.declare_partials('geometry:fuselage_Lpax', [
                              'cabin:LSeco', 'cabin:Wexit'], method='fd')
        self.declare_partials('geometry:fuselage_length',
                              ['cabin:front_seat_number_eco', 'cabin:Waisle',
                               'cabin:LSeco', 'cabin:WSeco', 'cabin:Wexit'], method='fd')
        self.declare_partials('geometry:fuselage_Lcabin',
                              ['cabin:front_seat_number_eco', 'cabin:Waisle',
                               'cabin:LSeco', 'cabin:WSeco', 'cabin:Wexit'], method='fd')
        self.declare_partials('cg_systems:C6',
                              ['cabin:front_seat_number_eco', 'cabin:WSeco',
                               'cabin:LSeco', 'cabin:Wexit', 'cabin:Waisle'], method='fd')
        self.declare_partials('cg_furniture:D2',
                              ['cabin:front_seat_number_eco', 'cabin:WSeco',
                               'cabin:LSeco', 'cabin:Wexit', 'cabin:Waisle'], method='fd')
        self.declare_partials('cg_pl:CG_PAX',
                              ['cabin:front_seat_number_eco', 'cabin:WSeco',
                               'cabin:LSeco', 'cabin:Wexit', 'cabin:Waisle'], method='fd')
        self.declare_partials('geometry:fuselage_wet_area',
                              ['cabin:front_seat_number_eco', 'cabin:Waisle',
                               'cabin:LSeco', 'cabin:WSeco', 'cabin:Wexit'], method='fd')

    def compute(self, inputs, outputs):
        front_seat_number_eco = inputs['cabin:front_seat_number_eco']
        ws_eco = inputs['cabin:WSeco']
        ls_eco = inputs['cabin:LSeco']
        w_aisle = inputs['cabin:Waisle']
        w_exit = inputs['cabin:Wexit']
        npax = inputs['tlar:NPAX']
        n_engines = inputs['geometry:engine_number']

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

        outputs['cabin:Nrows'] = n_rows
        outputs['cabin:NPAX1'] = npax_1
        outputs['cg_systems:C6'] = x_cg_c6
        outputs['cg_furniture:D2'] = x_cg_d2
        outputs['cg_pl:CG_PAX'] = x_cg_d2
        outputs['geometry:fuselage_length'] = fus_length
        outputs['geometry:fuselage_width_max'] = b_f
        outputs['geometry:fuselage_height_max'] = h_f
        outputs['geometry:fuselage_LAV'] = lav
        outputs['geometry:fuselage_LAR'] = lar
        outputs['geometry:fuselage_Lpax'] = lpax
        outputs['geometry:fuselage_Lcabin'] = cabin_length
        outputs['cabin:PNC'] = pnc
        outputs['geometry:fuselage_wet_area'] = wet_area_fus
