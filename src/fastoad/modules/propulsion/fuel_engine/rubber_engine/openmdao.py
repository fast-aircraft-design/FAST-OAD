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

from fastoad.modules.propulsion import OMIEngine, IEngineSubclass
from .rubber_engine import RubberEngine


class OMRubberEngine(OMIEngine):
    """
    Parametric engine model as OpenMDAO component

    See :class:`RubberEngine` for more information.
    """

    def setup(self):
        super().setup()
        self.add_input('propulsion:rubber_engine:bypass_ratio', np.nan)
        self.add_input('propulsion:rubber_engine:overall_pressure_ratio', np.nan)
        self.add_input('propulsion:rubber_engine:turbine_inlet_temperature', np.nan, units='K')
        self.add_input('propulsion:mto_thrust', np.nan, units='N')
        self.add_input('propulsion:rubber_engine:maximum_mach', np.nan)
        self.add_input('propulsion:rubber_engine:design_altitude', np.nan, units='m')
        self.add_input('propulsion:rubber_engine:delta_t4_climb', -50,
                       desc='As it is a delta, unit is K or °C, but is not '
                            'specified to avoid OpenMDAO making unwanted conversion')
        self.add_input('propulsion:rubber_engine:delta_t4_cruise', -100,
                       desc='As it is a delta, unit is K or °C, but is not '
                            'specified to avoid OpenMDAO making unwanted conversion')

    @staticmethod
    def get_engine(inputs) -> IEngineSubclass:
        """

        :param inputs: input parameters that define the engine
        :return: an :class:`RubberEngine` instance
        """
        param_names = ['bypass_ratio', 'overall_pressure_ratio',
                       'turbine_inlet_temperature', 'maximum_mach', 'design_altitude',
                       'delta_t4_climb', 'delta_t4_cruise']
        engine_params = {name: inputs['propulsion:rubber_engine:%s' % name] for name in param_names}

        param_names = ['mto_thrust']
        engine_params.update({name: inputs['propulsion:%s' % name] for name in param_names})

        return RubberEngine(**engine_params)
