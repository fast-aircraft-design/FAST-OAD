"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

from fastoad.geometry.geom_components.vt.components.compute_vt_distance import ComputeVTDistance
from fastoad.geometry.geom_components.vt.components.compute_vt_clalpha import ComputeVTClalpha
from fastoad.geometry.geom_components.vt.components.compute_cn_beta import ComputeCnBeta
from fastoad.geometry.geom_components.vt.components.compute_vt_area import ComputeVTArea
from fastoad.geometry.geom_components.vt.components.compute_vt_vol_coeff import ComputeVTVolCoeff
from fastoad.geometry.geom_components.vt.components.compute_vt_chords import ComputeVTChords
from fastoad.geometry.geom_components.vt.components.compute_vt_mac import ComputeVTMAC
from fastoad.geometry.geom_components.vt.components.compute_vt_cg import ComputeVTcg
from fastoad.geometry.geom_components.vt.components.compute_vt_sweep import ComputeVTSweep

from openmdao.api import Group

class ComputeVerticalTailGeometry(Group):
    
    def initialize(self):
        self.options.declare('deriv_method', default='fd')

        self.options.declare('tail_type', types=float, default=0.)
        self.options.declare('ac_family', types=float, default=1.0)
        
    def setup(self):
        deriv_method = self.options['deriv_method']

        self.tail_type = self.options['tail_type']
        self.ac_family = self.options['ac_family']
        
        self.add_subsystem('vt_aspect_ratio', ComputeVTDistance(tail_type=self.tail_type,
                                                                   ac_family=self.ac_family, deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('vt_clalpha', ComputeVTClalpha(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('cn_beta', ComputeCnBeta(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('vt_area', ComputeVTArea(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('vt_vol_coeff', ComputeVTVolCoeff(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('vt_chords', ComputeVTChords(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('vt_mac', ComputeVTMAC(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('vt_cg', ComputeVTcg(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('vt_sweep', ComputeVTSweep(deriv_method=deriv_method), promotes=['*'])