"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

from fastoad.geometry.geom_components.wing.components.compute_y_wing import ComputeYwing
from fastoad.geometry.geom_components.wing.components.compute_l1_l4 import ComputeL1AndL4Wing
from fastoad.geometry.geom_components.wing.components.compute_l2_l3 import ComputeL2AndL3Wing
from fastoad.geometry.geom_components.wing.components.compute_x_wing import ComputeXWing
from fastoad.geometry.geom_components.wing.components.compute_mac_wing import ComputeMACWing
from fastoad.geometry.geom_components.wing.components.compute_b_50 import ComputeB50
from fastoad.geometry.geom_components.wing.components.compute_sweep_wing import ComputeSweepWing
from fastoad.geometry.geom_components.wing.components.compute_toc_wing import ComputeToCWing
from fastoad.geometry.geom_components.wing.components.compute_wet_area_wing import ComputeWetAreaWing
from fastoad.geometry.geom_components.wing.components.compute_cl_alpha import ComputeCLalpha
from fastoad.geometry.geom_components.wing.components.compute_mfw import ComputeMFW
from fastoad.geometry.geom_components.wing.components.wing_drawing import WingDrawing

from openmdao.api import Group

class ComputeWingGeometry(Group):
    def initialize(self):
        self.options.declare('deriv_method', default='fd')
        self.options.declare('display_flag', default=False, types=bool)

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.display = self.options['display_flag']
        
        self.add_subsystem('y_wing', ComputeYwing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('l14_wing', ComputeL1AndL4Wing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('l2l3_wing', ComputeL2AndL3Wing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('x_wing', ComputeXWing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('mac_wing', ComputeMACWing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('b50_wing', ComputeB50(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('sweep_wing', ComputeSweepWing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('toc_wing', ComputeToCWing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('wetarea_wing', ComputeWetAreaWing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('clapha_wing', ComputeCLalpha(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('mfw', ComputeMFW(deriv_method=deriv_method), promotes=['*'])

        if self.display:
            self.add_subsystem('wing_drawing', WingDrawing(), promotes=['*'])