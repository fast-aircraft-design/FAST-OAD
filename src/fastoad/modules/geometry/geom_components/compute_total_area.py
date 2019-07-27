"""
    Estimation of total aircraft wet area
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
from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeTotalArea(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Total aircraft wet area estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_wet_area', val=200., units='m**2')
        self.add_input('geometry:fuselage_wet_area', val=400., units='m**2')
        self.add_input('geometry:ht_wet_area', val=100., units='m**2')
        self.add_input('geometry:vt_wet_area', val=100., units='m**2')
        self.add_input('geometry:nacelle_wet_area', val=50., units='m**2')
        self.add_input('geometry:pylon_wet_area', val=50., units='m**2')
        self.add_input('geometry:engine_number', val=2.)
        
        self.add_output('geometry:S_total', val=800., units='m**2')
        
        self.declare_partials('geometry:S_total', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        wet_area_wing = inputs['geometry:wing_wet_area']
        wet_area_fus = inputs['geometry:fuselage_wet_area']
        wet_area_ht = inputs['geometry:ht_wet_area']
        wet_area_vt = inputs['geometry:vt_wet_area']
        wet_area_nac = inputs['geometry:nacelle_wet_area']
        wet_area_pylon = inputs['geometry:pylon_wet_area']
        n_engines = inputs['geometry:engine_number']
        
        wet_area_total = wet_area_wing + wet_area_fus + wet_area_ht + wet_area_vt + \
            n_engines * (wet_area_nac + wet_area_pylon)

        outputs['geometry:S_total'] = wet_area_total 