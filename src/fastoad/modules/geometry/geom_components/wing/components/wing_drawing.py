"""
    Estimation of wing Xs
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
        
        self.add_input('geometry:wing_x4', val=np.nan)
        self.add_input('geometry:wing_y2', val=np.nan)
        self.add_input('geometry:wing_y3', val=np.nan)
        self.add_input('geometry:wing_y4', val=np.nan)
        self.add_input('geometry:wing_l2', val=np.nan)
        self.add_input('geometry:wing_l4', val=np.nan)
        
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