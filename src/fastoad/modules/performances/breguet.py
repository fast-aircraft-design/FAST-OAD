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

from fastoad.constants import FlightPhase
from fastoad.utils.physics import Atmosphere

CLIMB_RATIO = 0.97  # = mass at end of climb / mass at start of climb
DESCENT_RATIO = 0.98  # = mass at end of descent / mass at start of descent
RESERVE_RATIO = 1.06
CLIMB_DESCENT_DISTANCE = 500  # in km, distance of climb + descent


class Breguet(om.Group):
    """
    Estimation of fuel consumption through Breguet formula with a rough estimate
    of climb and descent phases
    """

    def initialize(self):
        self.options.declare('flight_point_count', 1, types=(int, tuple))

    def setup(self):
        self.add_subsystem('propulsion',
                           _BreguetPropulsion(
                               flight_point_count=self.options['flight_point_count']),
                           promotes=['*'])
        self.add_subsystem('breguet',
                           _ExplicitBreguet(flight_point_count=self.options['flight_point_count']),
                           promotes=['*'])


class ImplicitBreguet(om.Group):
    """
    Estimation of fuel consumption through Breguet formula with a rough estimate
    of climb and descent phases
    """

    def initialize(self):
        self.options.declare('flight_point_count', 1, types=(int, tuple))

    def setup(self):
        self.add_subsystem('propulsion',
                           _BreguetPropulsion(
                               flight_point_count=self.options['flight_point_count']),
                           promotes=['*'])
        self.add_subsystem('breguet',
                           _ImplicitBreguet(flight_point_count=self.options['flight_point_count']),
                           promotes=['*'])

        self.nonlinear_solver = om.NewtonSolver()
        self.linear_solver = om.DirectSolver()


class _BreguetPropulsion(om.ExplicitComponent):
    """
    Link with engine computation
    """

    def initialize(self):
        self.options.declare('flight_point_count', 1, types=(int, tuple))

    def setup(self):
        shape = self.options['flight_point_count']
        self.add_input('sizing_mission:cruise_altitude', np.nan, shape=shape, units='m')
        self.add_input('tlar:cruise_Mach', np.nan, shape=shape)
        self.add_input('weight:MTOW', np.nan, units='kg')
        self.add_input('aerodynamics:L_D_max', np.nan, shape=shape)
        self.add_input('engine_count', 2)

        self.add_output('propulsion:phase', FlightPhase.CRUISE)
        self.add_output('propulsion:use_thrust_rate', False)
        self.add_output('propulsion:required_thrust_rate', 0.)
        self.add_output('propulsion:required_thrust', units='N')
        self.add_output('propulsion:altitude', units='m')
        self.add_output('propulsion:mach')

        self.declare_partials('propulsion:phase', '*', method='fd')
        self.declare_partials('propulsion:use_thrust_rate', '*', method='fd')
        self.declare_partials('propulsion:required_thrust_rate', '*', method='fd')
        self.declare_partials('propulsion:required_thrust', '*', method='fd')
        self.declare_partials('propulsion:altitude', 'sizing_mission:cruise_altitude', method='fd')
        self.declare_partials('propulsion:mach', 'tlar:cruise_Mach', method='fd')

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        engine_count = inputs['engine_count']
        ld_ratio = inputs['aerodynamics:L_D_max']
        mtow = inputs['weight:MTOW']
        initial_cruise_mass = mtow * CLIMB_RATIO

        # Variables for propulsion
        outputs['propulsion:altitude'] = inputs['sizing_mission:cruise_altitude']
        outputs['propulsion:mach'] = inputs['tlar:cruise_Mach']

        outputs['propulsion:required_thrust'] = initial_cruise_mass / ld_ratio * g / engine_count


class _ExplicitBreguet(om.ExplicitComponent):
    """
    Estimation of fuel consumption through Breguet formula with a rough estimate
    of climb and descent phases
    """

    def initialize(self):
        self.options.declare('flight_point_count', 1, types=(int, tuple))

    def setup(self):
        shape = self.options['flight_point_count']
        self.add_input('sizing_mission:cruise_altitude', np.nan, shape=shape, units='m')
        self.add_input('tlar:cruise_Mach', np.nan, shape=shape)
        self.add_input('aerodynamics:L_D_max', np.nan, shape=shape)
        self.add_input('propulsion:SFC', np.nan, shape=shape, units='kg/N/s')
        self.add_input('tlar:Range', np.nan, shape=shape, units='m')
        self.add_input('weight:MTOW', np.nan, units='kg')

        self.add_output('mission:MZFW', units='kg')
        self.add_output('mission:fuel_weight', units='kg')

        self.declare_partials('mission:MZFW', '*', method='fd')
        self.declare_partials('mission:fuel_weight', '*', method='fd')

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        # pylint: disable=too-many-locals  # Cleaner than using directly inputs['...']
        atmosphere = Atmosphere(inputs['sizing_mission:cruise_altitude'], altitude_in_feet=False)
        cruise_speed = atmosphere.speed_of_sound * inputs['tlar:cruise_Mach']

        flight_range = inputs['tlar:Range']
        ld_ratio = inputs['aerodynamics:L_D_max']
        mtow = inputs['weight:MTOW']
        sfc = inputs['propulsion:SFC']

        range_factor = cruise_speed * ld_ratio / g / sfc
        cruise_distance = flight_range - CLIMB_DESCENT_DISTANCE * 1000
        cruise_mass_ratio = 1. / np.exp(cruise_distance / range_factor)
        flight_mass_ratio = cruise_mass_ratio * CLIMB_RATIO * DESCENT_RATIO

        mzfw = mtow * flight_mass_ratio / RESERVE_RATIO
        outputs['mission:fuel_weight'] = mtow - mzfw
        outputs['mission:MZFW'] = mzfw


class _ImplicitBreguet(om.ImplicitComponent):
    """
    Estimation of fuel consumption through Breguet formula with a rough estimate
    of climb and descent phases
    """

    def initialize(self):
        self.options.declare('flight_point_count', 1, types=(int, tuple))

    def setup(self):
        shape = self.options['flight_point_count']
        self.add_input('sizing_mission:cruise_altitude', np.nan, shape=shape, units='m')
        self.add_input('tlar:cruise_Mach', np.nan, shape=shape)
        self.add_input('aerodynamics:L_D_max', np.nan, shape=shape)
        self.add_input('propulsion:SFC', 1e-5, shape=shape, units='kg/N/s')
        self.add_input('tlar:Range', np.nan, shape=shape, units='m')
        self.add_input('engine_count', 2)
        self.add_input('weight:OEW', np.nan, units='kg')
        self.add_input('weight:Max_PL', np.nan, units='kg')

        self.add_output('weight:MTOW', 100000, units='kg')

        self.declare_partials('weight:MTOW', '*', method='fd')

    def apply_nonlinear(self, inputs, outputs, residuals,
                        discrete_inputs=None, discrete_outputs=None):
        # pylint: disable=too-many-arguments  # It's OpenMDAO's fault :)
        # pylint: disable=too-many-locals  # Ok, it's my fault, but it's cleaner this way
        atmosphere = Atmosphere(inputs['sizing_mission:cruise_altitude'], altitude_in_feet=False)
        cruise_speed = atmosphere.speed_of_sound * inputs['tlar:cruise_Mach']

        oew = inputs['weight:OEW']
        max_payload_weight = inputs['weight:Max_PL']
        flight_range = inputs['tlar:Range']
        ld_ratio = inputs['aerodynamics:L_D_max']
        mtow = outputs['weight:MTOW']
        sfc = inputs['propulsion:SFC']

        range_factor = cruise_speed * ld_ratio / g / sfc
        cruise_distance = flight_range - CLIMB_DESCENT_DISTANCE * 1000
        cruise_mass_ratio = 1. / np.exp(cruise_distance / range_factor)
        flight_mass_ratio = cruise_mass_ratio * CLIMB_RATIO * DESCENT_RATIO

        mzfw = mtow * flight_mass_ratio / RESERVE_RATIO

        mission_oew = mzfw - max_payload_weight
        residuals['weight:MTOW'] = oew - mission_oew

    def guess_nonlinear(self, inputs, outputs, residuals,
                        discrete_inputs=None, discrete_outputs=None):
        # pylint: disable=too-many-arguments # It's OpenMDAO's fault :)
        outputs['weight:MTOW'] = inputs['weight:OEW'] * 1.5
