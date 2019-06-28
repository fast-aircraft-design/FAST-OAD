"""
    Estimation of geometry of horizontal tail
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
from fastoad.modules.geometry.geom_components.ht.components import ComputeHTVolCoeff
from fastoad.modules.geometry.geom_components.ht.components import ComputeHTArea
from fastoad.modules.geometry.geom_components.ht.components import ComputeHTChord
from fastoad.modules.geometry.geom_components.ht.components import ComputeHTMAC
from fastoad.modules.geometry.geom_components.ht.components import ComputeHTcg
from fastoad.modules.geometry.geom_components.ht.components import ComputeHTSweep
from fastoad.modules.geometry.geom_components.ht.components import ComputeHTClalpha

from openmdao.api import Group

class ComputeHorizontalTailGeometry(Group):
    """ Horizontal tail geometry estimation """
    
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