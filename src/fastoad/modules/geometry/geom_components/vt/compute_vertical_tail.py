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
from openmdao.api import Group

from fastoad.modules.geometry.geom_components.vt.components.compute_vt_distance \
    import ComputeVTDistance
from fastoad.modules.geometry.geom_components.vt.components.compute_vt_clalpha \
    import ComputeVTClalpha
from fastoad.modules.geometry.geom_components.vt.components.compute_cn_beta \
    import ComputeCnBeta
from fastoad.modules.geometry.geom_components.vt.components.compute_vt_area \
    import ComputeVTArea
from fastoad.modules.geometry.geom_components.vt.components.compute_vt_vol_coeff \
    import ComputeVTVolCoeff
from fastoad.modules.geometry.geom_components.vt.components.compute_vt_chords \
    import ComputeVTChords
from fastoad.modules.geometry.geom_components.vt.components.compute_vt_mac \
    import ComputeVTMAC
from fastoad.modules.geometry.geom_components.vt.components.compute_vt_cg \
    import ComputeVTcg
from fastoad.modules.geometry.geom_components.vt.components.compute_vt_sweep \
    import ComputeVTSweep

from fastoad.modules.geometry.options import AIRCRAFT_FAMILY_OPTION, TAIL_TYPE_OPTION


class ComputeVerticalTailGeometry(Group):
    """ Vertical tail geometry estimation """

    def initialize(self):

        self.options.declare(TAIL_TYPE_OPTION, types=float, default=0.)
        self.options.declare(AIRCRAFT_FAMILY_OPTION, types=float, default=1.0)

        self.tail_type = self.options[TAIL_TYPE_OPTION]
        self.ac_family = self.options[AIRCRAFT_FAMILY_OPTION]

    def setup(self):

        self.add_subsystem('vt_aspect_ratio',
                           ComputeVTDistance(tail_type=self.tail_type,
                                             ac_family=self.ac_family), promotes=['*'])
        self.add_subsystem('vt_clalpha',
                           ComputeVTClalpha(), promotes=['*'])
        self.add_subsystem('cn_beta',
                           ComputeCnBeta(), promotes=['*'])
        self.add_subsystem('vt_area',
                           ComputeVTArea(), promotes=['*'])
        self.add_subsystem('vt_vol_coeff',
                           ComputeVTVolCoeff(), promotes=['*'])
        self.add_subsystem('vt_chords',
                           ComputeVTChords(), promotes=['*'])
        self.add_subsystem('vt_mac',
                           ComputeVTMAC(), promotes=['*'])
        self.add_subsystem('vt_cg',
                           ComputeVTcg(), promotes=['*'])
        self.add_subsystem('vt_sweep',
                           ComputeVTSweep(), promotes=['*'])
