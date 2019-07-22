"""
    FAST - Copyright (c) 2016 ONERA ISAE
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

import math
import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent
from scipy import interpolate


class ComputeDeltaHighLift(ExplicitComponent):

    def initialize(self):
        self.options.declare('resources_dir',
                             default=os.path.join(os.path.dirname(__file__), os.pardir, os.pardir,
                                                  'resources'),
                             types=str)
        self.options.declare('landing_flag', default=False, types=bool)

    def setup(self):
        self.resourcesdir = self.options['resources_dir']
        self.landing = self.options['landing_flag']

        if self.landing == True:
            self.add_input('sizing_mission:flap_angle_landing', val=np.nan)
            self.add_input('sizing_mission:slat_angle_landing', val=np.nan)
            self.add_output('delta_cl_landing', val=np.nan)
        else:
            self.add_input('sizing_mission:flap_angle_to', val=np.nan)
            self.add_input('sizing_mission:slat_angle_to', val=np.nan)
            self.add_output('delta_cl_takeoff', val=np.nan)
            self.add_output('delta_cd_takeoff', val=np.nan)

        self.add_input('geometry:wing_sweep_0', val=np.nan)
        self.add_input('geometry:wing_sweep_100_outer', val=np.nan)
        self.add_input('geometry:flap_chord_ratio', val=np.nan)
        self.add_input('geometry:flap_span_ratio', val=np.nan)
        self.add_input('geometry:slat_chord_ratio', val=np.nan)
        self.add_input('geometry:slat_span_ratio', val=np.nan)
        self.add_input('xfoil:mach', val=np.nan)

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
        if self.landing == True:
            flap_angle = inputs['sizing_mission:flap_angle_landing']
            slat_angle = inputs['sizing_mission:slat_angle_landing']
            Mach = inputs['xfoil:mach']
        else:
            flap_angle = inputs['sizing_mission:flap_angle_to']
            slat_angle = inputs['sizing_mission:slat_angle_to']
            Mach = 0.2

        le_angle = inputs['geometry:wing_sweep_0']
        tl_angle = inputs['geometry:wing_sweep_100_outer']
        flap_chord_ratio = inputs['geometry:flap_chord_ratio']
        flap_span_ratio = inputs['geometry:flap_span_ratio']
        slat_chord_ratio = inputs['geometry:slat_chord_ratio']
        slat_span_ratio = inputs['geometry:slat_span_ratio']

        flap_angle = flap_angle / 180 * math.pi
        slat_angle = slat_angle / 180 * math.pi

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
                         math.cos(tl_angle / 180. * math.pi) + delta_cl_slat * slat_span_ratio * \
                         math.cos(
                             le_angle / 180. * math.pi)  # this equation is from ref Raymer book

        cd0_flap = (-0.01523 + 0.05145 * flap_angle - 9.53201E-4 * flap_angle ** 2 +
                    7.5972E-5 * flap_angle ** 3) * \
                   flap_span_ratio / 100
        cd0_slat = (-0.00266 + 0.06065 * slat_angle - 0.03023 * slat_angle ** 2 +
                    0.01055 * slat_angle ** 3 - 0.00176 * slat_angle ** 4 +
                    1.77986E-4 * slat_angle ** 5 - 1.11754E-5 * slat_angle ** 6 +
                    4.19082E-7 * slat_angle ** 7 - 8.53492E-9 * slat_angle ** 8 +
                    7.24194E-11 * slat_angle ** 9) * \
                   slat_span_ratio / 100
        total_cd0 = cd0_flap + cd0_slat

        if self.landing:
            outputs['delta_cl_landing'] = delta_cl_total
        else:
            outputs['delta_cl_takeoff'] = delta_cl_total
            outputs['delta_cd_takeoff'] = total_cd0

    def compute_alpha_flap(self, flap_angle, ratio_cf_flap):
        f_vsp = os.path.join(self.resourcesdir,
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
