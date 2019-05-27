"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeTotalArea(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_wet_area', val=200.)
        self.add_input('geometry:fuselage_wet_area', val=400.)
        self.add_input('geometry:ht_wet_area', val=100.)
        self.add_input('geometry:vt_wet_area', val=100.)
        self.add_input('geometry:nacelle_wet_area', val=50.)
        self.add_input('geometry:pylon_wet_area', val=50.)
        self.add_input('geometry:engine_number', val=2.)
        
        self.add_output('geometry:S_total', val=800.)
        
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