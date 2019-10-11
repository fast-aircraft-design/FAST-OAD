"""
    Estimation of wing ToC
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
import os
import math
import numpy as np

from openmdao.core.explicitcomponent import ExplicitComponent

from fastoad.modules.geometry.functions import airfoil_reshape


class ComputeToCWing(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing ToC estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('tlar:cruise_Mach', val=np.nan)
        self.add_input('geometry:wing_sweep_25', val=np.nan, units='deg')

        self.add_output('geometry:wing_toc_aero')
        self.add_output('geometry:wing_toc_root')
        self.add_output('geometry:wing_toc_kink')
        self.add_output('geometry:wing_toc_tip')

        self.declare_partials('geometry:wing_toc_aero', '*', method=deriv_method)
        self.declare_partials('geometry:wing_toc_root', '*', method=deriv_method)
        self.declare_partials('geometry:wing_toc_kink', '*', method=deriv_method)
        self.declare_partials('geometry:wing_toc_tip', '*', method=deriv_method)

    def compute(self, inputs, outputs):
        cruise_mach = inputs['tlar:cruise_Mach']
        sweep_25 = inputs['geometry:wing_sweep_25']

        # Relative thickness
        el_aero = 0.89 - (cruise_mach + 0.02) * math.sqrt(math.cos(sweep_25 / 180. * math.pi))
        el_emp = 1.24 * el_aero
        el_break = 0.94 * el_aero
        el_ext = 0.86 * el_aero

        #Airfoil reshape according toc in different sections
        f_path_resources = os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir,
                                        os.pardir, os.pardir, 'resources')
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
