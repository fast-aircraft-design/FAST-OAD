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
import numpy as np
from math import sqrt

from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeFuselageGeometry(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Geometry of fuselase part A - Cabin (Commercial) estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

#        self.add_input('cabin:cabin_sizing', val=np.nan)
        self.add_input('cabin:WSeco', val=np.nan)
        self.add_input('cabin:LSeco', val=np.nan)
        self.add_input('cabin:front_seat_number_eco', val=np.nan)
        self.add_input('cabin:Waisle', val=np.nan)
        self.add_input('cabin:Wexit', val=np.nan)
        self.add_input('tlar:NPAX', val=np.nan)
        # self.add_input('cabin:Nrows', val=np.nan)
#        self.add_input('geometry:fuselage_length', val=np.nan)
#        self.add_input('geometry:fuselage_width_max', val=np.nan)
#        self.add_input('geometry:fuselage_height_max', val=np.nan)
#        self.add_input('geometry:fuselage_LAV', val=np.nan)
#        self.add_input('geometry:fuselage_LAR', val=np.nan)
#        self.add_input('geometry:fuselage_Lpax', val=np.nan)
        self.add_input('geometry:engine_number', val=np.nan)

        self.add_output('cabin:NPAX1')
        self.add_output('cabin:Nrows')
        self.add_output('cg_systems:C6')
        self.add_output('cg_furniture:D2')
        self.add_output('cg_pl:CG_PAX')
        self.add_output('geometry:fuselage_length')
        self.add_output('geometry:fuselage_width_max')
        self.add_output('geometry:fuselage_height_max')
        self.add_output('geometry:fuselage_LAV')
        self.add_output('geometry:fuselage_LAR')
        self.add_output('geometry:fuselage_Lpax')
        self.add_output('geometry:fuselage_Lcabin')
        self.add_output('geometry:fuselage_wet_area')
        self.add_output('cabin:PNC')

        self.declare_partials('cabin:NPAX1', ['tlar:NPAX'], method=deriv_method)
        self.declare_partials('cabin:Nrows', ['cabin:front_seat_number_eco',
                                                              'tlar:NPAX'], method=deriv_method)
        self.declare_partials('geometry:fuselage_width_max', ['cabin:front_seat_number_eco', 'cabin:WSeco',
                                                              'cabin:Waisle'], method=deriv_method)
        self.declare_partials('geometry:fuselage_height_max', ['cabin:front_seat_number_eco', 'cabin:WSeco',
                                                               'cabin:Waisle'], method=deriv_method)
        self.declare_partials('geometry:fuselage_LAV', ['cabin:front_seat_number_eco', 'cabin:WSeco',
                                                        'cabin:Waisle'], method=deriv_method)
        self.declare_partials('geometry:fuselage_LAR', ['cabin:front_seat_number_eco', 'cabin:WSeco',
                                                        'cabin:Waisle'], method=deriv_method)
        self.declare_partials('geometry:fuselage_Lpax', [
                              'cabin:LSeco', 'cabin:Wexit'], method=deriv_method)
        self.declare_partials('geometry:fuselage_length', ['cabin:front_seat_number_eco', 'cabin:Waisle',
                                                           'cabin:LSeco', 'cabin:WSeco', 'cabin:Wexit'], method=deriv_method)
        self.declare_partials('geometry:fuselage_Lcabin', ['cabin:front_seat_number_eco', 'cabin:Waisle',
                                                           'cabin:LSeco', 'cabin:WSeco', 'cabin:Wexit'], method=deriv_method)
        self.declare_partials('cg_systems:C6', ['cabin:front_seat_number_eco', 'cabin:WSeco',
                                                'cabin:LSeco', 'cabin:Wexit', 'cabin:Waisle'], method=deriv_method)
        self.declare_partials('cg_furniture:D2', ['cabin:front_seat_number_eco', 'cabin:WSeco',
                                                  'cabin:LSeco', 'cabin:Wexit', 'cabin:Waisle'], method=deriv_method)
        self.declare_partials('cg_pl:CG_PAX', ['cabin:front_seat_number_eco', 'cabin:WSeco',
                                               'cabin:LSeco', 'cabin:Wexit', 'cabin:Waisle'], method=deriv_method)
        self.declare_partials('geometry:fuselage_wet_area', ['cabin:front_seat_number_eco', 'cabin:Waisle',
                                                             'cabin:LSeco', 'cabin:WSeco', 'cabin:Wexit'], method=deriv_method)

    def compute(self, inputs, outputs):
        cabin_sizing = True
        front_seat_number_eco = inputs['cabin:front_seat_number_eco']
        WSeco = inputs['cabin:WSeco']
        LSeco = inputs['cabin:LSeco']
        Waisle = inputs['cabin:Waisle']
        Wexit = inputs['cabin:Wexit']
        NPAX = inputs['tlar:NPAX']
        n_engines = inputs['geometry:engine_number']

        if cabin_sizing:
            # Cabin width = N * seat width + Aisle width + (N+2)*2"+2 * 1"
            wcabin = front_seat_number_eco * WSeco + \
                Waisle + (front_seat_number_eco + 2) * 0.051 + 0.05

            # Number of rows = Npax / N
            npax_1 = int(1.05 * NPAX)
            Nrows = int(npax_1 / front_seat_number_eco)
            pnc = int((NPAX+17)/35)
            # Length of pax cabin = Length of seat area + Width of 1 Emergency
            # exits
            lpax = (Nrows * LSeco) + 1 * Wexit
            l_cyl = lpax - (2 * front_seat_number_eco - 4) * LSeco
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
            x_cg_c6 = lav - (front_seat_number_eco - 4) * LSeco + lpax * 0.1
            x_cg_d2 = lav - (front_seat_number_eco - 4) * LSeco + lpax / 2

            outputs['cabin:Nrows'] = Nrows 
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
        else:
            npax_1 = inputs['tlar:NPAX']
            fus_length = inputs['geometry:fus_length']
            b_f = self.aircraft.vars_geometry['geometry:fuselage_width_max']
            h_f = self.aircraft.vars_geometry['geometry:fuselage_height_max']
            lav = self.aircraft.vars_geometry['geometry:fuselage_LAV']
            lar = self.aircraft.vars_geometry['geometry:fuselage_LAR']
            lpax = self.aircraft.vars_geometry['geometry:fuselage_Lpax']
            cabin_length = 0.81 * fus_length
            x_cg_passenger = lav + lpax/2.0
            x_cg_d2 = lav + 0.35*lpax
            x_cg_c6 = lav + 0.1*lpax
            pnc = int((npax_1+17)/35)
            outputs['cabin:NPAX1'] = npax_1
            outputs['cg_pl:CG_PAX'] = x_cg_passenger
            outputs['cg_systems:C6'] = x_cg_c6
            outputs['cg_furniture:D2'] = x_cg_d2
            outputs['geometry:fuselage_length'] = fus_length
            outputs['geometry:fuselage_width_max'] = b_f
            outputs['geometry:fuselage_height_max'] = h_f
            outputs['geometry:fuselage_LAV'] = lav
            outputs['geometry:fuselage_LAR'] = lar
            outputs['geometry:fuselage_Lpax'] = lpax
            outputs['geometry:fuselage_Lcabin'] = cabin_length
            outputs['cabin:PNC'] = pnc

        # equivalent diameter of the fuselage
        fus_dia = sqrt(b_f * h_f)
#        cyl_length = fus_length - lav - lar
        wet_area_nose = 2.45 * fus_dia * lav
        wet_area_cyl = 3.1416 * fus_dia * l_cyl
        wet_area_tail = 2.3 * fus_dia * lar
        wet_area_fus = (wet_area_nose + wet_area_cyl + wet_area_tail)

        outputs['geometry:fuselage_wet_area'] = wet_area_fus
