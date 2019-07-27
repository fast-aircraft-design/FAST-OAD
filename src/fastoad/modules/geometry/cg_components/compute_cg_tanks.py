"""
    Estimation of tanks center of gravity
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
import os 
import math
from scipy import interpolate 

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeTanksCG(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Tanks center of gravity estimation """

    def initialize(self):
        self.options.declare('ratio', default=0.2, types=float)
        
    def setup(self):
        self.ratio = self.options['ratio']
        self.add_input('geometry:wing_front_spar_ratio_root', val=np.nan)
        self.add_input('geometry:wing_front_spar_ratio_kink', val=np.nan)
        self.add_input('geometry:wing_front_spar_ratio_tip', val=np.nan)
        self.add_input('geometry:wing_rear_spar_ratio_root', val=np.nan)
        self.add_input('geometry:wing_rear_spar_ratio_kink', val=np.nan)
        self.add_input('geometry:wing_rear_spar_ratio_tip', val=np.nan)
        self.add_input('geometry:wing_l0', val=np.nan, units='m')
        self.add_input('geometry:wing_x0', val=np.nan, units='m')
        self.add_input('geometry:wing_l2', val=np.nan, units='m')
        self.add_input('geometry:wing_l3', val=np.nan, units='m')
        self.add_input('geometry:wing_l4', val=np.nan, units='m')
        self.add_input('geometry:wing_y2', val=np.nan, units='m')
        self.add_input('geometry:wing_x3', val=np.nan, units='m')
        self.add_input('geometry:wing_y3', val=np.nan, units='m')
        self.add_input('geometry:wing_x4', val=np.nan, units='m')
        self.add_input('geometry:wing_y4', val=np.nan, units='m')
        self.add_input('geometry:wing_position', val=np.nan, units='m')      
        self.add_input('geometry:fuselage_width_max', val=np.nan, units='m')
        
        self.add_output('cg:cg_tank', units='m')
        
        self.declare_partials('cg:cg_tank', '*', method='fd')
        
    def compute(self, inputs, outputs):
        x_up = []
        x_down = []
        y_up = []
        y_down = []
        xy_up = []
        xy_down = []
        front_spar_ratio_root = inputs['geometry:wing_front_spar_ratio_root']
        front_spar_ratio_kink = inputs['geometry:wing_front_spar_ratio_kink']
        front_spar_ratio_tip = inputs['geometry:wing_front_spar_ratio_tip']
        rear_spar_ratio_root = inputs['geometry:wing_rear_spar_ratio_root']
        rear_spar_ratio_kink = inputs['geometry:wing_rear_spar_ratio_kink']
        rear_spar_ratio_tip = inputs['geometry:wing_rear_spar_ratio_tip']
        l0_wing = inputs['geometry:wing_l0']
        x0_wing = inputs['geometry:wing_x0']
        l2_wing = inputs['geometry:wing_l2']
        l3_wing = inputs['geometry:wing_l3']
        l4_wing = inputs['geometry:wing_l4']
        y2_wing = inputs['geometry:wing_y2']
        x3_wing = inputs['geometry:wing_x3']
        y3_wing = inputs['geometry:wing_y3']
        y4_wing = inputs['geometry:wing_y4']
        x4_wing = inputs['geometry:wing_x4']
        fa_length = inputs['geometry:wing_position']
        width_max = inputs['geometry:fuselage_width_max']

        f_airfoil = os.path.join(
            os.path.dirname(__file__), os.pardir, 'resources', 'airfoil_f_15_15.dat')
        airfoil_file = open(f_airfoil, 'r')
        node_number = int(airfoil_file.readline())
        for _ in range(1, node_number):
            line = airfoil_file.readline()
            xy_up.append([float(xy) for xy in line.split(',')])
        for _ in range(node_number + 1):
            line = airfoil_file.readline()
            xy_down.append([float(xy) for xy in line.split(',')])
        airfoil_file.close()
        for xy_u in xy_up:
            x_up.append(xy_u[0])
            y_up.append(xy_u[1])
        for xy_d in xy_down:
            x_down.append(xy_d[0])
            y_down.append(xy_d[1])
        y_up_root_front = interpolate.interp1d(x_up, y_up)(front_spar_ratio_root)
        y_down_root_front = interpolate.interp1d(x_down, y_down)(front_spar_ratio_root)
        y_up_root_rear = interpolate.interp1d(x_up, y_up)(rear_spar_ratio_root)
        y_down_root_rear = interpolate.interp1d(x_down, y_down)(rear_spar_ratio_root)
        height_root_front = (y_up_root_front - y_down_root_front) * l2_wing
        height_root_rear = (y_up_root_rear - y_down_root_rear) * l2_wing
        x_up = []
        x_down = []
        y_up = []
        y_down = []
        xy_up = []
        xy_down = []
        f_airfoil = os.path.join(
            os.path.dirname(__file__), os.pardir, 'resources', 'airfoil_f_15_12.dat')
        airfoil_file = open(f_airfoil, 'r')
        node_number = int(airfoil_file.readline())
        for _ in range(1, node_number):
            line = airfoil_file.readline()
            xy_up.append([float(xy) for xy in line.split(',')])
        for _ in range(node_number + 1):
            line = airfoil_file.readline()
            xy_down.append([float(xy) for xy in line.split(',')])
        airfoil_file.close()
        for xy_u in xy_up:
            x_up.append(xy_u[0])
            y_up.append(xy_u[1])
        for xy_d in xy_down:
            x_down.append(xy_d[0])
            y_down.append(xy_d[1])
        y_up_kink_front = interpolate.interp1d(x_up, y_up)(front_spar_ratio_kink)
        y_down_kink_front = interpolate.interp1d(x_down, y_down)(front_spar_ratio_kink)
        y_up_kink_rear = interpolate.interp1d(x_up, y_up)(rear_spar_ratio_kink)
        y_down_kink_rear = interpolate.interp1d(x_down, y_down)(rear_spar_ratio_kink)
        height_kink_front = (y_up_kink_front - y_down_kink_front) * l3_wing
        height_kink_rear = (y_up_kink_rear - y_down_kink_rear) * l3_wing

        x_up = []
        x_down = []
        y_up = []
        y_down = []
        xy_up = []
        xy_down = []
        f_airfoil = os.path.join(
            os.path.dirname(__file__), os.pardir, 'resources', 'airfoil_f_15_11.dat')
        airfoil_file = open(f_airfoil, 'r')
        node_number = int(airfoil_file.readline())
        for _ in range(1, node_number):
            line = airfoil_file.readline()
            xy_up.append([float(xy) for xy in line.split(',')])
        for _ in range(node_number + 1):
            line = airfoil_file.readline()
            xy_down.append([float(xy) for xy in line.split(',')])
        airfoil_file.close()
        for xy_u in xy_up:
            x_up.append(xy_u[0])
            y_up.append(xy_u[1])
        for xy_d in xy_down:
            x_down.append(xy_d[0])
            y_down.append(xy_d[1])
        y_up_tip_front = interpolate.interp1d(x_up, y_up)(front_spar_ratio_tip)
        y_down_tip_front = interpolate.interp1d(x_down, y_down)(front_spar_ratio_tip)
        y_up_tip_rear = interpolate.interp1d(x_up, y_up)(rear_spar_ratio_tip)
        y_down_tip_rear = interpolate.interp1d(x_down, y_down)(rear_spar_ratio_tip)
        height_tip_front = (y_up_tip_front - y_down_tip_front) * l4_wing
        height_tip_rear = (y_up_tip_rear - y_down_tip_rear) * l4_wing

        l_root = l2_wing * (rear_spar_ratio_root - front_spar_ratio_root)
        l_kink = l3_wing * (rear_spar_ratio_kink - front_spar_ratio_kink)

        l_tip = l4_wing * (rear_spar_ratio_tip - front_spar_ratio_tip)
        s_root = (height_root_front + height_root_rear) * l_root / 2
        s_kink = (height_kink_front + height_kink_rear) * l_kink / 2
        s_tip = (height_tip_front + height_tip_rear) * l_tip / 2
        vol_central = s_root * width_max
        vol_side_inner = (s_root + s_kink + math.sqrt(s_root * s_kink)) * \
            (y3_wing - y2_wing) * 2 / 3
        # Assume in the region ourward 0.8 of the span, no tank installed
        ratio_1 = y4_wing * self.ratio / (y4_wing - y3_wing)
        s_real_tip = (ratio_1 * (s_kink**0.5 - s_tip**0.5) + s_tip**0.5)**2
        vol_side_out = (s_kink + s_real_tip +
                        math.sqrt(s_kink *
                                  s_real_tip)) * (y4_wing - y3_wing) * (1 - ratio_1) * 2 / 3
#        vol_side = vol_side_inner + vol_side_out
        # assume only 80% of the total volume can be used for fuel, based on Raymer(0.85),
        # for central tank, the ratio is 0.92 fuel density is 785kg/m3
#        total_mass = (vol_side * 0.8 + vol_central * 0.92) * 785
        #######################################################################
        # CG calculation of tank
        x_cg_central = l_root / 3 * (height_root_front + 2 * height_root_rear) / (
            height_root_front + height_root_rear) + l2_wing * front_spar_ratio_root
        x_cg_central_absolute = fa_length - 0.25 * l0_wing - x0_wing + x_cg_central

        y_side_inner_cg = (y3_wing - y2_wing) / \
            4 * (s_root + 3 * s_kink + 2 *
                 math.sqrt(s_root * s_kink)) / (s_root + s_kink + math.sqrt(s_root * s_kink))
        height_side_inner_cg_front = (y_side_inner_cg / (y3_wing - y2_wing)) * (
            height_kink_front - height_root_front) + height_root_front
        height_side_inner_cg_rear = (
            y_side_inner_cg / (y3_wing - y2_wing)) * \
            (height_kink_rear - height_root_rear) + height_root_rear
        l_side_inner_cg = (
            y_side_inner_cg / (y3_wing - y2_wing)) * (l_kink - l_root) + l_root
        x_side_inner_front = (y_side_inner_cg /
                              (y3_wing - y2_wing)) * \
            (x3_wing + l3_wing *
             front_spar_ratio_kink - l2_wing * front_spar_ratio_root) + \
            l2_wing * front_spar_ratio_root
        x_cg_side_inner = x_side_inner_front + l_side_inner_cg / 3 * (
            height_side_inner_cg_front + 2 * height_side_inner_cg_rear) / (
            height_side_inner_cg_front + height_side_inner_cg_rear)
        x_cg_side_inner_absolute = fa_length - 0.25 * l0_wing - x0_wing + x_cg_side_inner

        y4_tank = y4_wing * (1 - self.ratio)
        x4_tank = (x4_wing - x3_wing) * (1 - y4_wing * self.ratio / (y4_wing - y3_wing)) + x3_wing
        l4_tank = l4_wing + (l3_wing - l4_wing) * ratio_1
        height_tank_front = height_tip_front + \
            (height_kink_front - height_tip_front) * ratio_1
        height_tank_rear = height_tip_rear + \
            (height_kink_rear - height_tip_rear) * ratio_1
        l_tank_tip = l_tip + (l_kink - l_tip) * ratio_1
        front_spar_ratio_tank = front_spar_ratio_tip + \
            (front_spar_ratio_kink - front_spar_ratio_tip) * ratio_1

        y_side_out_cg = (y4_tank - y3_wing) / 4 * (s_kink + 3 * s_real_tip + 2 * math.sqrt(
            s_kink * s_real_tip)) / (s_kink + s_real_tip + math.sqrt(s_kink * s_real_tip))
        height_side_out_cg_front = (y_side_out_cg / (y4_tank - y3_wing)) * \
            (height_tank_front - height_kink_front) + height_kink_front
        height_side_out_cg_rear = (
            y_side_out_cg / (y4_tank - y3_wing)) * (height_tank_rear -
                                                    height_kink_rear) + height_kink_rear
        l_side_out_cg = (y_side_out_cg / (y4_tank - y3_wing)) * \
            (l_tank_tip - l_kink) + l_kink
        x_side_out_front = (y_side_out_cg /
                            (y4_tank - y3_wing)) * (x4_tank + l4_tank * front_spar_ratio_tank -
                                                    x3_wing - l3_wing * front_spar_ratio_kink) + \
            x3_wing + l3_wing * front_spar_ratio_kink
        x_cg_side_out = x_side_out_front + l_side_out_cg / 3 * \
            (height_side_out_cg_front + 2 * height_side_out_cg_rear) / \
            (height_side_out_cg_front + height_side_out_cg_rear)
        x_cg_side_out_absolute = fa_length - \
            0.25 * l0_wing - x0_wing + x_cg_side_out

        x_cg_tank = (vol_side_out * 0.8 * x_cg_side_out_absolute +
                     vol_side_inner * 0.8 * x_cg_side_inner_absolute +
                     vol_central * 0.92 * x_cg_central_absolute) / \
            (vol_side_out * 0.8 + vol_side_inner *
             0.8 + vol_central * 0.92)
        # x_cg_tank=(vol_side_out*0.8*x_cg_side_out+vol_side_inner
        # *0.8*x_cg_side_inner+vol_central*0.8*x_cg_central)/
        # (vol_side_out*0.8+vol_side_inner*0.8+vol_central*0.8)

        outputs['cg:cg_tank'] = x_cg_tank