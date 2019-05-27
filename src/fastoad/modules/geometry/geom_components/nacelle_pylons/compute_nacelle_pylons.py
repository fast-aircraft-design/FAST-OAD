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
import numpy as np
from math import sqrt 

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeNacelleAndPylonsGeometry(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Nacelle and pylon geometry estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

        self.options.declare('engine_location', types=float, default=1.0)
        self.options.declare('ac_family', types=float, default=1.0)
    
    def setup(self):
        deriv_method = self.options['deriv_method']

        self.engine_loc = self.options['engine_location']
        self.ac_family = self.options['ac_family']
        
#        self.add_input('geometry:engine_sizing', val=np.nan)
        self.add_input('propulsion_conventional:thrust_SL', val=np.nan)
#        self.add_input('geometry:nacelle_length', val=np.nan)
#        self.add_input('geometry:nacelle_dia', val=np.nan)
#        self.add_input('geometry:LG_height', val=np.nan)
        self.add_input('geometry:y_ratio_engine', val=np.nan)
        self.add_input('geometry:wing_span', val=np.nan)
        self.add_input('geometry:wing_l0', val=np.nan)
        self.add_input('geometry:wing_x0', val=np.nan)
        self.add_input('geometry:wing_l2', val=np.nan)
        self.add_input('geometry:wing_y2', val=np.nan)
        self.add_input('geometry:wing_l3', val=np.nan)
        self.add_input('geometry:wing_y3', val=np.nan)
        self.add_input('geometry:wing_x3', val=np.nan)
        self.add_input('geometry:wing_position', val=np.nan)
        self.add_input('geometry:fuselage_length', val=np.nan)
        self.add_input('geometry:fuselage_width_max', val=np.nan)

        self.add_output('geometry:pylon_length')
        self.add_output('geometry:fan_length')
        self.add_output('geometry:nacelle_length')
        self.add_output('geometry:nacelle_dia')
        self.add_output('geometry:LG_height')
        self.add_output('geometry:y_nacell')
        self.add_output('geometry:pylon_wet_area')
        self.add_output('geometry:nacelle_wet_area')
        self.add_output('cg_propulsion:B1')
        
        self.declare_partials('geometry:nacelle_dia', 'propulsion_conventional:thrust_SL', method=deriv_method)
        self.declare_partials('geometry:nacelle_length', 'propulsion_conventional:thrust_SL', method=deriv_method)
        self.declare_partials('geometry:LG_height', 'propulsion_conventional:thrust_SL', method=deriv_method)
        self.declare_partials('geometry:fan_length', 'propulsion_conventional:thrust_SL', method=deriv_method)
        self.declare_partials('geometry:pylon_length', 'propulsion_conventional:thrust_SL', method=deriv_method)
        self.declare_partials('geometry:y_nacell', ['propulsion_conventional:thrust_SL', 
                                                    'geometry:fuselage_width_max',
                                                    'geometry:y_ratio_engine',
                                                    'geometry:wing_span'], method=deriv_method)
        self.declare_partials('cg_propulsion:B1', ['geometry:wing_position', 'geometry:wing_l0', 'geometry:wing_x0',
                                                   'geometry:wing_x3', 'geometry:wing_y2', 'geometry:wing_y3',
                                                   'geometry:wing_l2', 'geometry:wing_l3', 'geometry:fuselage_length',
                                                   'propulsion_conventional:thrust_SL', 'geometry:fuselage_width_max',
                                                   'geometry:y_ratio_engine', 'geometry:wing_span'], method=deriv_method)
        self.declare_partials('geometry:nacelle_wet_area', 'propulsion_conventional:thrust_SL', method=deriv_method)
        self.declare_partials('geometry:pylon_wet_area', 'propulsion_conventional:thrust_SL', method=deriv_method)
            
    def compute(self, inputs, outputs):
        thrust_SL = inputs['propulsion_conventional:thrust_SL']
        y_ratio_engine = inputs['geometry:y_ratio_engine']
        span = inputs['geometry:wing_span']
        l0_wing = inputs['geometry:wing_l0']
        x0_wing = inputs['geometry:wing_x0']
        l2_wing = inputs['geometry:wing_l2']
        y2_wing = inputs['geometry:wing_y2']
        l3_wing = inputs['geometry:wing_l3']
        x3_wing = inputs['geometry:wing_x3']
        y3_wing = inputs['geometry:wing_y3']
        fa_length = inputs['geometry:wing_position']
        fus_length = inputs['geometry:fuselage_length']
        b_f = inputs['geometry:fuselage_width_max']
        
        nac_dia = 0.00904 * sqrt(thrust_SL * 0.225) + 0.7
        lg_height = 1.4 * nac_dia
        # The nominal thrust must be used in lbf
        nac_length = 0.032 * sqrt(thrust_SL * 0.225)
            
        outputs['geometry:nacelle_length'] = nac_length            
        outputs['geometry:nacelle_dia'] = nac_dia
        outputs['geometry:LG_height'] = lg_height
               
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
            
        outputs['geometry:pylon_length'] = pylon_length    
        outputs['geometry:fan_length'] = fan_length
        outputs['geometry:y_nacell'] = y_nacell
        outputs['cg_propulsion:B1'] = x_nacell_cg_absolute
        
        #Wet surfaces 
        wet_area_nac = 0.0004 * thrust_SL * 0.225 + 11      # By engine
        wet_area_pylon = 0.35 * wet_area_nac
        
        outputs['geometry:nacelle_wet_area'] = wet_area_nac
        outputs['geometry:pylon_wet_area'] = wet_area_pylon