"""
Computation of lift increment due to high-lift devices
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

import os
import os.path as pth

import math
import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent
from scipy import interpolate


class DeltaCLHighLift(ExplicitComponent):
    # TODO: Document equations. Cite sources (see self.compute() for draft version)
    """
    Component for getting lift increment for given Mach and slat/flap configuration
    """

    def initialize(self):
        self.options.declare('resources_dir',
                             default=pth.join(os.path.dirname(__file__), 'resources'),
                             types=str)

    def setup(self):
        self.add_input('flap_angle', val=np.nan, units='rad')
        self.add_input('slat_angle', val=np.nan, units='rad')
        self.add_output('delta_cl', val=np.nan)

        self.add_input('geometry:wing_sweep_0', val=np.nan, units='rad')
        self.add_input('geometry:wing_sweep_100_outer', val=np.nan, units='rad')
        self.add_input('geometry:flap_chord_ratio', val=np.nan)
        self.add_input('geometry:flap_span_ratio', val=np.nan)
        self.add_input('geometry:slat_chord_ratio', val=np.nan)
        self.add_input('geometry:slat_span_ratio', val=np.nan)
        self.add_input('mach', val=np.nan)

    def compute(self, inputs, outputs):
        """  Calculates the cl produced by flap and slat.
    
            Method based on Roskam book and Raymer book
            ---------------------------------------------------------------
                                parameter definition of deta_cl_highlift
            ---------------------------------------------------------------
            name              definition discription
            flap_angle     |  the angle of flap that deployed, depend on the configuration of takeoff
            slat_angle     |  the angle of slat that deployed, depend on the configuration of takeoff
            Mach           |  Mach number of the aircraft
            le_angle       |  sweep angle at leading edge
            tl_angle       |  sweep angle at trailing edge
            ratio_c_flap   |  ratio of chord with flap extended compared to clean chord
            deta_cl_flap   |  cl created by the flap two dimension
            ratio_c_slat   |  ratio of chord with slat extended compared to clean chord
            cl_deta        |  leading edge slat effectivness
            deta_cl_slat   |  cl created by the slat, two dimensional
            deta_cl_total  |  cl due to flap and slat including 3D
            ratio_cf_flap  |  average ratio of flap chord to clean chord,
                           |  here we use 0.197 from CeRas(deduced from wing geometry)
            ratio_cf_slat  |  average ratio of slat chord to clean chord, here we use 0.177
                           |  from CeRas(deduced from wing geometry)
            sf_s           |  the ratio of the part of of wing who has flap,
                           |  see detail in French document, 0.8 is a typical number
            ss_s           |  the ratio of the part of of wing who has
            slat, see detail in French document, 0.9 is a typical number
        """
        flap_angle = inputs['flap_angle']
        slat_angle = inputs['slat_angle']
        Mach = inputs['mach']

        le_angle = inputs['geometry:wing_sweep_0']
        tl_angle = inputs['geometry:wing_sweep_100_outer']
        flap_chord_ratio = inputs['geometry:flap_chord_ratio']
        flap_span_ratio = inputs['geometry:flap_span_ratio']
        slat_chord_ratio = inputs['geometry:slat_chord_ratio']
        slat_span_ratio = inputs['geometry:slat_span_ratio']

        ratio_c_flap = (1. + flap_chord_ratio * math.cos(flap_angle))

        alpha_flap = self.compute_alpha_flap(
            flap_angle *
            57.3,
            flap_chord_ratio)

        delta_cl_flap = 2. * math.pi / \
                        math.sqrt(1 - Mach ** 2) * ratio_c_flap * alpha_flap * flap_angle

        ratio_c_slat = (1. + slat_chord_ratio * math.cos(slat_angle))

        cl_delta = 5.05503E-7 + 0.00666 * slat_chord_ratio + 0.23758 * \
                   slat_chord_ratio ** 2 - 4.3639 * slat_chord_ratio ** 3 + \
                   51.16323 * slat_chord_ratio ** 4 - 320.10803 * \
                   slat_chord_ratio ** 5 + 1142.23033 * slat_chord_ratio ** 6 - \
                   2340.75209 * slat_chord_ratio ** 7 + 2570.35947 * \
                   slat_chord_ratio ** 8 - 1173.73465 * slat_chord_ratio ** 9

        delta_cl_slat = cl_delta * slat_angle * 57.3 * ratio_c_slat
        delta_cl_total = delta_cl_flap * flap_span_ratio * \
                         math.cos(tl_angle) + delta_cl_slat * slat_span_ratio * \
                         math.cos(le_angle)  # this equation is from ref Raymer book

        outputs['delta_cl'] = delta_cl_total

    def compute_alpha_flap(self, flap_angle, ratio_cf_flap):
        f_vsp = os.path.join(self.options['resources_dir'],
                             'interpolation of lift effectiveness.txt')
        temp_array = []
        fichier = open(f_vsp, "r")
        for line in fichier:
            temp_array.append([float(x) for x in line.split(',')])
        fichier.close()
        x1 = []
        y1 = []
        x2 = []
        y2 = []
        x3 = []
        y3 = []
        x4 = []
        y4 = []
        x5 = []
        y5 = []

        for arr in temp_array:
            x1.append(arr[0])
            y1.append(arr[1])
            x2.append(arr[2])
            y2.append(arr[3])
            x3.append(arr[4])
            y3.append(arr[5])
            x4.append(arr[6])
            y4.append(arr[7])
            x5.append(arr[8])
            y5.append(arr[9])

        tck1 = interpolate.splrep(x1, y1, s=0)
        tck2 = interpolate.splrep(x2, y2, s=0)
        tck3 = interpolate.splrep(x3, y3, s=0)
        tck4 = interpolate.splrep(x4, y4, s=0)
        tck5 = interpolate.splrep(x5, y5, s=0)
        ynew1 = interpolate.splev(flap_angle, tck1, der=0)
        ynew2 = interpolate.splev(flap_angle, tck2, der=0)
        ynew3 = interpolate.splev(flap_angle, tck3, der=0)
        ynew4 = interpolate.splev(flap_angle, tck4, der=0)
        ynew5 = interpolate.splev(flap_angle, tck5, der=0)
        zs = [0.15, 0.20, 0.25, 0.30, 0.40]
        y_final = [ynew1, ynew2, ynew3, ynew4, ynew5]
        tck6 = interpolate.splrep(zs, y_final, s=0)
        return interpolate.splev(ratio_cf_flap, tck6, der=0)
