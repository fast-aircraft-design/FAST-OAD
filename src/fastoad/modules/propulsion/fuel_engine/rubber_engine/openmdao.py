"""
OpenMDAO wrapping of RubberEngine
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

from .rubber_engine import RubberEngine


class _OMRubberEngine(om.ExplicitComponent):
    """
    Base class for the parametric engine model as OpenMDAO component

    See :class:`RubberEngine` for more information.
    """

    def initialize(self):
        self.options.declare('flight_point_count', 1)

    def setup(self):
        self.add_input('bypass_ratio', np.nan)
        self.add_input('overall_pressure_ratio', np.nan)
        self.add_input('turbine_inlet_temperature', np.nan, units='K')
        self.add_input('mto_thrust', np.nan, units='N')
        self.add_input('maximum_mach', np.nan)
        self.add_input('design_altitude', np.nan, units='m')
        self.add_input('delta_t4_climb', -50, units='K')
        self.add_input('delta_t4_cruise', -100, units='K')

        shape = (self.options['flight_point_count'],)
        self.add_input('mach', np.nan, shape=shape)
        self.add_input('altitude', np.nan, shape=shape, units='m')
        self.add_input('phase', np.nan, shape=shape)

        self.add_output('SFC', np.nan, shape=shape, units='kg/s/N')
        self.declare_partials('SFC', '*', method='fd')

    @staticmethod
    def get_engine(inputs):
        """

        :param inputs: input parameters that define the engine
        :return: an :class:`RubberEngine` instance
        """
        param_names = ['bypass_ratio', 'overall_pressure_ratio',
                       'turbine_inlet_temperature',
                       'mto_thrust', 'maximum_mach', 'design_altitude', 'delta_t4_climb',
                       'delta_t4_cruise']
        engine_params = {name: inputs[name] for name in param_names}
        return RubberEngine(**engine_params)


class RegulatedRubberEngine(_OMRubberEngine):
    """
    OpenMDAO component for a parametric engine model that is driven by required thrust

    See :class:`RubberEngine` for more information.
    """

    def setup(self):
        super().setup()
        shape = (self.options['flight_point_count'],)
        self.add_input('thrust', np.nan, shape=shape, units='N')
        self.add_output('thrust_rate', np.nan, shape=shape)
        self.declare_partials('thrust_rate', '*', method='fd')

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        engine = self.get_engine(inputs)
        sfc, thrust_rate = engine.compute_regulated(inputs['mach'], inputs['altitude'],
                                                    inputs['thrust'], inputs['phase'])
        outputs['SFC'] = sfc
        outputs['thrust_rate'] = thrust_rate


class ManualRubberEngine(_OMRubberEngine):
    """
    OpenMDAO component for a parametric engine model that is driven by thrust rate

    See :class:`RubberEngine` for more information.
    """

    def setup(self):
        super().setup()
        shape = (self.options['flight_point_count'],)
        self.add_input('thrust_rate', np.nan, shape=shape)
        self.add_output('thrust', np.nan, shape=shape, units='N')
        self.declare_partials('thrust', '*', method='fd')

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        engine = self.get_engine(inputs)
        sfc, thrust = engine.compute_manual(inputs['mach'], inputs['altitude'],
                                            inputs['thrust_rate'], inputs['phase'])
        outputs['SFC'] = sfc
        outputs['thrust'] = thrust
