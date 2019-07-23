"""
Computation of lift and drag increment due to high-lift devices
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

import warnings

import numpy as np
from openmdao.components.add_subtract_comp import AddSubtractComp
from openmdao.core.group import Group

from fastoad.modules.aerodynamics.components.high_lift_drag import DeltaCDHighLift
from .high_lift_lift import DeltaCLHighLift


class ComputeDeltaHighLift(Group):
    """
    Combines DeltaCDHighLift and DeltaCLHighLift
    """

    # TODO: use directly DeltaCDHighLift and DeltaCLHighLift
    def initialize(self):
        warnings.warn(DeprecationWarning('use DeltaCDHighLift and DeltaCLHighLift instead'))
        self.options.declare('landing_flag', default=False, types=bool)

    def setup(self):

        link_inputs = AddSubtractComp()
        link_inputs.add_equation('mach', 'xfoil:mach')
        if self.options['landing_flag']:
            link_inputs.add_equation('slat_angle', 'sizing_mission:slat_angle_landing', val=np.nan,
                                     units='deg')
            link_inputs.add_equation('flap_angle', 'sizing_mission:flap_angle_landing', val=np.nan,
                                     units='deg')
        else:
            link_inputs.add_equation('slat_angle', 'sizing_mission:slat_angle_to', val=np.nan,
                                     units='deg')
            link_inputs.add_equation('flap_angle', 'sizing_mission:flap_angle_to', val=np.nan,
                                     units='deg')

        self.add_subsystem('link_inputs', link_inputs, promotes=['*'])

        self.add_subsystem('delta_cl', DeltaCLHighLift(), promotes=['*'])
        if not self.options['landing_flag']:
            self.add_subsystem('delta_cd', DeltaCDHighLift(), promotes=['*'])

        link_outputs = AddSubtractComp()
        if self.options['landing_flag']:
            link_outputs.add_equation('delta_cl_landing', 'delta_cl')
        else:
            link_outputs.add_equation('delta_cl_takeoff', 'delta_cl')
            link_outputs.add_equation('delta_cd_takeoff', 'delta_cd')

        self.add_subsystem('link_outputs', link_outputs, promotes=['*'])
