"""
Aero computation for landing phase
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

from fastoad.modules.aerodynamics.components.compute_max_cl_landing import ComputeMaxClLanding
from fastoad.modules.aerodynamics.components.high_lift_aero import ComputeDeltaHighLift
from fastoad.modules.aerodynamics.external.xfoil import XfoilPolar
from fastoad.utils.physics import Atmosphere


class AerodynamicsLanding(om.Group):

    def initialize(self):
        self.options.declare('use_xfoil', default=True, types=bool)

    def setup(self):
        self.add_subsystem('mach_reynolds', ComputeMachReynolds(), promotes=['*'])
        if self.options['use_xfoil']:
            self.add_subsystem('xfoil_run', XfoilPolar(),
                               promotes=['geometry:wing:sweep_25',
                                         'geometry:wing:thickness_ratio'])
        self.add_subsystem('delta_cl_landing', ComputeDeltaHighLift(landing_flag=True),
                           promotes=['*'])
        self.add_subsystem('compute_max_cl_landing', ComputeMaxClLanding(), promotes=['*'])

        if self.options['use_xfoil']:
            self.connect('aerodynamics:aircraft:landing:mach', 'xfoil_run.xfoil:mach')
            self.connect('aerodynamics:aircraft:landing:reynolds', 'xfoil_run.xfoil:reynolds')
            self.connect('xfoil_run.xfoil:CL_max_clean',
                         'aerodynamics:aircraft:landing:CL_max_clean')


class ComputeMachReynolds(om.ExplicitComponent):

    def setup(self):
        self.add_input('geometry:wing:MAC:length', val=np.nan, units='m')
        self.add_input('TLAR:approach_speed', val=np.nan, units='m/s')
        self.add_output('aerodynamics:aircraft:landing:mach')
        self.add_output('aerodynamics:aircraft:landing:reynolds')

        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        l0_wing = inputs['geometry:wing:MAC:length']
        speed = inputs['TLAR:approach_speed']

        atm = Atmosphere(0., 15.)
        mach = speed / atm.speed_of_sound
        reynolds = atm.get_unitary_reynolds(mach) * l0_wing

        outputs['aerodynamics:aircraft:landing:mach'] = mach
        outputs['aerodynamics:aircraft:landing:reynolds'] = reynolds
