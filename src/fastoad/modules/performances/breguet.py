"""
Simple module for performances
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
import openmdao.api as om
from scipy.constants import g

from fastoad.utils.physics import Atmosphere

CLIMB_RATIO = 0.97  # = mass at end of climb / mass at start of climb
DESCENT_RATIO = 0.98  # = mass at end of descent / mass at start of descent
RESERVE_RATIO = 1.06
CLIMB_DESCENT_DISTANCE = 500  # in km, distance of climb + descent


class Breguet(om.ExplicitComponent):
    """
    Estimation of fuel consumption through Breguet formula with a rough estimate
    of climb and descent phases
    """

    def initialize(self):
        self.options.declare('flight_point_count', 1, types=(int, tuple))

    def setup(self):
        shape = self.options['flight_point_count']
        self.add_input('altitude', np.nan, shape=shape, units='m')
        self.add_input('mach', np.nan, shape=shape)
        self.add_input('lift_to_drag_ratio', np.nan, shape=shape)
        self.add_input('SFC', np.nan, shape=shape, units='kg/N/s')
        self.add_input('flight_distance', np.nan, shape=shape, units='m')
        self.add_input('MTOW', np.nan, units='kg')
        self.add_input('engine_count', 2)

        self.add_output('MZFW', units='kg')
        self.add_output('fuel_weight', units='kg')
        self.add_output('use_thrust_rate', False)
        self.add_output('required_thrust_rate', 0.)
        self.add_output('required_thrust', units='N')

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        atmosphere = Atmosphere(inputs['altitude'], altitude_in_feet=False)
        cruise_speed = atmosphere.speed_of_sound * inputs['mach']

        initial_cruise_mass = inputs['MTOW'] * CLIMB_RATIO
        outputs['required_thrust'] = initial_cruise_mass / inputs['lift_to_drag_ratio'] * g \
                                     / inputs['engine_count']
        range_factor = cruise_speed * inputs['lift_to_drag_ratio'] / g / inputs['SFC']
        cruise_distance = inputs['flight_distance'] - CLIMB_DESCENT_DISTANCE * 1000
        cruise_mass_ratio = 1. / np.exp(cruise_distance / range_factor)
        flight_mass_ratio = cruise_mass_ratio * CLIMB_RATIO * DESCENT_RATIO
        outputs['MZFW'] = inputs['MTOW'] * flight_mass_ratio / RESERVE_RATIO
        outputs['fuel_weight'] = inputs['MTOW'] - outputs['MZFW']
