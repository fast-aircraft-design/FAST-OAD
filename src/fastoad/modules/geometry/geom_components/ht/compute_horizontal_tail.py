"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

from fastoad.geometry.geom_components.ht.components.compute_ht_vol_coeff import ComputeHTVolCoeff
from fastoad.geometry.geom_components.ht.components.compute_ht_area import ComputeHTArea
from fastoad.geometry.geom_components.ht.components.compute_ht_chords import ComputeHTChord
from fastoad.geometry.geom_components.ht.components.compute_ht_mac import ComputeHTMAC
from fastoad.geometry.geom_components.ht.components.compute_ht_cg import ComputeHTcg
from fastoad.geometry.geom_components.ht.components.compute_ht_sweep import ComputeHTSweep
from fastoad.geometry.geom_components.ht.components.compute_ht_cl_alpha import ComputeHTClalpha

from openmdao.api import Group

class ComputeHorizontalTailGeometry(Group):
    
    def initialize(self):
        self.options.declare('deriv_method', default='fd')
        self.options.declare('tail_type', types=float, default=0.)
        self.options.declare('ac_family', types=float, default=1.0)    

    def setup(self):
        deriv_method = self.options['deriv_method']
        self.tail_type = self.options['tail_type']
        self.ac_family = self.options['ac_family']
        
        self.add_subsystem('ht_vol_coeff', ComputeHTVolCoeff(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('ht_area', ComputeHTArea(tail_type=self.tail_type,
                                                    ac_family=self.ac_family, deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('ht_chord', ComputeHTChord(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('ht_mac', ComputeHTMAC(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('ht_cg', ComputeHTcg(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('ht_sweep', ComputeHTSweep(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('ht_cl_alpha', ComputeHTClalpha(deriv_method=deriv_method), promotes=['*'])