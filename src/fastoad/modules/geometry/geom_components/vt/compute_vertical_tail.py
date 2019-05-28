"""
    Estimation of geometry of vertical tail
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
    """ Vertical tail geometry estimation """
    
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