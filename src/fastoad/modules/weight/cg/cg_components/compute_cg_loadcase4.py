"""
    Estimation of center of gravity for load case 4
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
from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeCGLoadCase4(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Center of gravity estimation for load case 4 """

    def setup(self):

        self.add_input('geometry:wing:MAC:length', val=np.nan, units='m')
        self.add_input('geometry:wing:MAC:x', val=np.nan, units='m')
        self.add_input('weight:payload:PAX:CG:x', val=np.nan, units='m')
        self.add_input('weight:payload:rear_fret:CG:x', val=np.nan, units='m')
        self.add_input('weight:payload:front_fret:CG:x', val=np.nan, units='m')
        self.add_input('TLAR:NPAX', val=np.nan)
        self.add_input('weight:aircraft_empty:CG:x', val=np.nan, units='m')
        self.add_input('weight:aircraft_empty:mass', val=np.nan, units='m')

        self.add_output('weight:aircraft:load_case_4:CG:ratio')

        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        l0_wing = inputs['geometry:wing:MAC:length']
        fa_length = inputs['geometry:wing:MAC:x']
        cg_pax = inputs['weight:payload:PAX:CG:x']
        cg_rear_fret = inputs['weight:payload:rear_fret:CG:x']
        cg_front_fret = inputs['weight:payload:front_fret:CG:x']
        npax = inputs['TLAR:NPAX']
        x_cg_plane_aft = inputs['weight:aircraft_empty:CG:x']
        x_cg_plane_down = inputs['weight:aircraft_empty:mass']
        x_cg_plane_up = x_cg_plane_aft * x_cg_plane_down

        weight_pax = npax * 90.
        weight_rear_fret = npax * 30.
        weight_front_fret = npax * 10.
        weight_pl = weight_pax + weight_rear_fret + weight_front_fret
        x_cg_pl_4 = (weight_pax * cg_pax +
                     weight_rear_fret * cg_rear_fret +
                     weight_front_fret *
                     cg_front_fret) / weight_pl
        x_cg_plane_pl_4 = (x_cg_plane_up + weight_pl * x_cg_pl_4) / \
            (x_cg_plane_down + weight_pl)  # forward
        cg_ratio_pl_4 = (x_cg_plane_pl_4 - fa_length + 0.25 * l0_wing) / l0_wing

        outputs['weight:aircraft:load_case_4:CG:ratio'] = cg_ratio_pl_4
