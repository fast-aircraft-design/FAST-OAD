"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import os 
import matplotlib.pyplot as plt

from openmdao.core.explicitcomponent import ExplicitComponent

class WingDrawing(ExplicitComponent):
    def initialize(self):
        self.options.declare('result_dir', 
                              default = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 
                                                     os.pardir, os.pardir, 'result'),
                              types=str)        
    def setup(self):
        self.result_dir = self.options['result_dir']
        
        self.add_input('geometry:wing_x4', val=16.)
        self.add_input('geometry:wing_y2', val=2.)
        self.add_input('geometry:wing_y3', val=6.)
        self.add_input('geometry:wing_y4', val=16.)
        self.add_input('geometry:wing_l2', val=6.)
        self.add_input('geometry:wing_l4', val=1.5)
        
    def compute(self, inputs, outputs):
        x = [0, inputs['geometry:wing_y2_wing'], inputs['geometry:wing_y4'], 
             inputs['geometry:wing_y4'], inputs['geometry:wing_y3'], 
             inputs['geometry:wing_y2'], 0, 0]
        y = [0, 0, inputs['geometry:wing_x4'], (inputs['geometry:wing_x4'] + inputs['geometry:wing_l4']),
             inputs['geometry:wing_l2'], inputs['geometry:wing_l2'], inputs['geometry:wing_l2'], 0]

        plt.figure(1, figsize=(8, 5))
        plt.plot(x, y)
        plt.title('Wing geometry')
        plt.axis([0, 18, 0, 11])
        plt.savefig(os.path.join(self.result_dir, 'Wing_Geometry.jpg'))
        plt.show()        