"""
Computation of wing area
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


class ComputeWingArea(om.Group):

    def setup(self):
        self.add_subsystem('wing_area', _ComputeWingArea(), promotes=['*'])
        self.add_subsystem('constraints', ComputeWingAreaConstraints(), promotes=['*'])


class _ComputeWingArea(om.ExplicitComponent):
    """ Computation of wing area from needed approach speed and mission fuel """

    def setup(self):
        self.add_input('geometry:wing:aspect_ratio', val=np.nan)
        self.add_input('geometry:wing:root:thickness_ratio', val=np.nan)
        self.add_input('geometry:wing:tip:thickness_ratio', val=np.nan)
        self.add_input('mission:sizing:trip:fuel', val=np.nan, units='kg')
        self.add_input('TLAR:approach_speed', val=np.nan, units='m/s')

        self.add_input('weight:aircraft:MLW', val=np.nan, units='kg')
        self.add_input('aerodynamics:aircraft:landing:CL_max', val=np.nan)

        self.add_output('geometry:wing:area', val=10., units='m**2')
        self.declare_partials('geometry:wing:area', '*', method='fd')

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        lambda_wing = inputs['geometry:wing:aspect_ratio']
        root_thickness_ratio = inputs['geometry:wing:root:thickness_ratio']
        tip_thickness_ratio = inputs['geometry:wing:tip:thickness_ratio']
        mfw_mission = inputs['mission:sizing:trip:fuel']
        wing_area_mission = ((mfw_mission - 1570) /
                             224 / lambda_wing ** -0.4 /
                             (0.6 * root_thickness_ratio + 0.4 * tip_thickness_ratio)
                             ) ** (1 / 1.5)

        approach_speed = inputs['TLAR:approach_speed']
        mlw = inputs['weight:aircraft:MLW']
        max_CL = inputs['aerodynamics:aircraft:landing:CL_max']
        wing_area_approach = 2 * mlw * 9.81 / ((approach_speed / 1.23) ** 2) / (1.225 * max_CL)

        outputs['geometry:wing:area'] = max(wing_area_mission, wing_area_approach)


class ComputeWingAreaConstraints(om.ExplicitComponent):

    def setup(self):
        self.add_input('mission:sizing:trip:fuel', val=np.nan, units='kg')
        self.add_input('weight:aircraft:MFW', val=np.nan, units='kg')

        self.add_input('TLAR:approach_speed', val=np.nan, units='m/s')
        self.add_input('weight:aircraft:MLW', val=np.nan, units='kg')
        self.add_input('aerodynamics:aircraft:landing:CL_max', val=np.nan)
        self.add_input('geometry:wing:area', val=np.nan, units='m**2')

        self.add_output('weight:aircraft:additional_fuel_capacity', units='kg')
        self.add_output('aerodynamics:aircraft:landing:additional_CL_capacity')

        self.declare_partials('weight:aircraft:additional_fuel_capacity',
                              ['weight:aircraft:MFW', 'mission:sizing:trip:fuel'],
                              method='fd')
        self.declare_partials('aerodynamics:aircraft:landing:additional_CL_capacity',
                              ['TLAR:approach_speed', 'weight:aircraft:MLW',
                               'aerodynamics:aircraft:landing:CL_max',
                               'geometry:wing:area'], method='fd')

    def compute(self, inputs, outputs):
        mfw = inputs['weight:aircraft:MFW']
        mission_fuel = inputs['mission:sizing:trip:fuel']
        v_approach = inputs['TLAR:approach_speed']
        cl_max = inputs['aerodynamics:aircraft:landing:CL_max']
        mlw = inputs['weight:aircraft:MLW']
        wing_area = inputs['geometry:wing:area']

        outputs['weight:aircraft:additional_fuel_capacity'] = mfw - mission_fuel
        outputs['aerodynamics:aircraft:landing:additional_CL_capacity'] = cl_max - mlw * 9.81 / (
                0.5 * 1.225 * (v_approach / 1.23) ** 2 * wing_area)
