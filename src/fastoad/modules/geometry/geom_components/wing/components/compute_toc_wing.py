"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

import os
import math

from fast.Geometry.functions.airfoil_reshape import airfoil_reshape

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeToCWing(ExplicitComponent):

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('tlar:cruise_Mach', val=0.78)
        self.add_input('geometry:wing_sweep_25', val=25.)
        
        self.add_output('geometry:wing_toc_aero', val=0.128)
        self.add_output('geometry:wing_toc_root', val=0.128)
        self.add_output('geometry:wing_toc_kink', val=0.128)
        self.add_output('geometry:wing_toc_tip', val=0.128)

        self.declare_partials('geometry:wing_toc_aero', '*', method=deriv_method)
        self.declare_partials('geometry:wing_toc_root', '*', method=deriv_method)
        self.declare_partials('geometry:wing_toc_kink', '*', method=deriv_method)
        self.declare_partials('geometry:wing_toc_tip', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        cruise_Mach = inputs['tlar:cruise_Mach']
        sweep_25 = inputs['geometry:wing_sweep_25']
        
        el_aero = 0.89 - (cruise_Mach + 0.02) * math.sqrt(math.cos(sweep_25 / 180. * math.pi))
        el_emp = 1.24 * el_aero
        el_break = 0.94 * el_aero
        el_ext = 0.86 * el_aero
        
        #Aifoil reshape according toc in different sections
        f_path_resources = os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir,
                                        os.pardir, os.pardir, os.pardir,'resources')
        f_path_ori = os.path.join(f_path_resources, 'BACJ.txt')
        f_path_root = os.path.join(f_path_resources, 'root.txt')
        f_path_kink = os.path.join(f_path_resources, 'kink.txt')
        f_path_tip = os.path.join(f_path_resources, 'tip.txt')
        airfoil_reshape(el_emp, f_path_ori, f_path_root)
        airfoil_reshape(el_break, f_path_ori, f_path_kink)
        airfoil_reshape(el_ext, f_path_ori, f_path_tip)
        
        outputs['geometry:wing_toc_aero'] = el_aero
        outputs['geometry:wing_toc_root'] = el_emp
        outputs['geometry:wing_toc_kink'] = el_break
        outputs['geometry:wing_toc_tip'] = el_ext
        