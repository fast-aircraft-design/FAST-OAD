"""
    Estimation of nacelle and pylon geometry
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
from math import sqrt

import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent

from fastoad.modules.geometry.options import AIRCRAFT_FAMILY_OPTION, ENGINE_LOCATION_OPTION


class ComputeNacelleAndPylonsGeometry(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Nacelle and pylon geometry estimation """

    def initialize(self):

        self.options.declare(ENGINE_LOCATION_OPTION, types=float, default=1.0)
        self.options.declare(AIRCRAFT_FAMILY_OPTION, types=float, default=1.0)

        self.engine_loc = self.options[ENGINE_LOCATION_OPTION]
        self.ac_family = self.options[AIRCRAFT_FAMILY_OPTION]

    def setup(self):

        self.add_input('propulsion:MTO_thrust', val=np.nan, units='N')
        self.add_input('geometry:propulsion:engine:y_ratio', val=np.nan)
        self.add_input('geometry:wing:span', val=np.nan, units='m')
        self.add_input('geometry:wing:MAC:length', val=np.nan, units='m')
        self.add_input('geometry:wing:root:leading_edge:x', val=np.nan, units='m')
        self.add_input('geometry:wing:root:chord', val=np.nan, units='m')
        self.add_input('geometry:wing:root:y', val=np.nan, units='m')
        self.add_input('geometry:wing:kink:chord', val=np.nan, units='m')
        self.add_input('geometry:wing:kink:y', val=np.nan, units='m')
        self.add_input('geometry:wing:kink:leading_edge:x', val=np.nan, units='m')
        self.add_input('geometry:wing:MAC:x', val=np.nan, units='m')
        self.add_input('geometry:fuselage:length', val=np.nan, units='m')
        self.add_input('geometry:fuselage:maximum_width', val=np.nan, units='m')

        self.add_output('geometry:propulsion:pylon:length', units='m')
        self.add_output('geometry:propulsion:fan:length', units='m')
        self.add_output('geometry:propulsion:nacelle:length', units='m')
        self.add_output('geometry:propulsion:nacelle:diameter', units='m')
        self.add_output('geometry:landing_gear:height', units='m')
        self.add_output('geometry:propulsion:nacelle:y', units='m')
        self.add_output('geometry:propulsion:pylon:wetted_area', units='m**2')
        self.add_output('geometry:propulsion:nacelle:wetted_area', units='m**2')
        self.add_output('weight:propulsion:engine:CG:x', units='m')

        self.declare_partials('geometry:propulsion:nacelle:diameter',
                              'propulsion:MTO_thrust', method='fd')
        self.declare_partials('geometry:propulsion:nacelle:length',
                              'propulsion:MTO_thrust', method='fd')
        self.declare_partials('geometry:landing_gear:height',
                              'propulsion:MTO_thrust', method='fd')
        self.declare_partials('geometry:propulsion:fan:length',
                              'propulsion:MTO_thrust', method='fd')
        self.declare_partials('geometry:propulsion:pylon:length',
                              'propulsion:MTO_thrust', method='fd')
        self.declare_partials('geometry:propulsion:nacelle:y',
                              ['propulsion:MTO_thrust',
                               'geometry:fuselage:maximum_width',
                               'geometry:propulsion:engine:y_ratio',
                               'geometry:wing:span'], method='fd')
        self.declare_partials('weight:propulsion:engine:CG:x',
                              ['geometry:wing:MAC:x',
                               'geometry:wing:MAC:length',
                               'geometry:wing:root:leading_edge:x',
                               'geometry:wing:kink:leading_edge:x',
                               'geometry:wing:root:y',
                               'geometry:wing:kink:y',
                               'geometry:wing:root:chord',
                               'geometry:wing:kink:chord',
                               'geometry:fuselage:length',
                               'propulsion:MTO_thrust',
                               'geometry:fuselage:maximum_width',
                               'geometry:propulsion:engine:y_ratio',
                               'geometry:wing:span'], method='fd')
        self.declare_partials('geometry:propulsion:nacelle:wetted_area',
                              'propulsion:MTO_thrust', method='fd')
        self.declare_partials('geometry:propulsion:pylon:wetted_area',
                              'propulsion:MTO_thrust', method='fd')

    def compute(self, inputs, outputs):
        thrust_sl = inputs['propulsion:MTO_thrust']
        y_ratio_engine = inputs['geometry:propulsion:engine:y_ratio']
        span = inputs['geometry:wing:span']
        l0_wing = inputs['geometry:wing:MAC:length']
        x0_wing = inputs['geometry:wing:root:leading_edge:x']
        l2_wing = inputs['geometry:wing:root:chord']
        y2_wing = inputs['geometry:wing:root:y']
        l3_wing = inputs['geometry:wing:kink:chord']
        x3_wing = inputs['geometry:wing:kink:leading_edge:x']
        y3_wing = inputs['geometry:wing:kink:y']
        fa_length = inputs['geometry:wing:MAC:x']
        fus_length = inputs['geometry:fuselage:length']
        b_f = inputs['geometry:fuselage:maximum_width']

        nac_dia = 0.00904 * sqrt(thrust_sl * 0.225) + 0.7  # FIXME: use output of engine module
        lg_height = 1.4 * nac_dia
        # The nominal thrust must be used in lbf
        nac_length = 0.032 * sqrt(thrust_sl * 0.225)  # FIXME: use output of engine module

        outputs['geometry:propulsion:nacelle:length'] = nac_length
        outputs['geometry:propulsion:nacelle:diameter'] = nac_dia
        outputs['geometry:landing_gear:height'] = lg_height

        fan_length = 0.60 * nac_length
        pylon_length = 1.1 * nac_length

        if self.engine_loc == 1:
            y_nacell = y_ratio_engine * span / 2
        elif self.engine_loc == 2:
            y_nacell = b_f/2. + 0.5*nac_dia

        l_wing_nac = l3_wing + (l2_wing - l3_wing) * (y3_wing - y_nacell) / (y3_wing - y2_wing)
        delta_x_nacell = 0.05 * l_wing_nac

        if self.engine_loc == 1:
            x_nacell_cg = x3_wing * (y_nacell - y2_wing) / (y3_wing - y2_wing) - \
                delta_x_nacell - 0.2 * nac_length
            x_nacell_cg_absolute = fa_length - 0.25 * l0_wing - (x0_wing - x_nacell_cg)
        elif self.engine_loc == 2:
            if self.ac_family == 1.0:
                x_nacell_cg_absolute = 0.8*fus_length
            elif self.ac_family == 2.0:
                x_nacell_cg_absolute = 0.8*fus_length-1.5

        outputs['geometry:propulsion:pylon:length'] = pylon_length
        outputs['geometry:propulsion:fan:length'] = fan_length
        outputs['geometry:propulsion:nacelle:y'] = y_nacell
        outputs['weight:propulsion:engine:CG:x'] = x_nacell_cg_absolute

        # Wet surfaces
        wet_area_nac = 0.0004 * thrust_sl * 0.225 + 11  # By engine
        wet_area_pylon = 0.35 * wet_area_nac

        outputs['geometry:propulsion:nacelle:wetted_area'] = wet_area_nac
        outputs['geometry:propulsion:pylon:wetted_area'] = wet_area_pylon
