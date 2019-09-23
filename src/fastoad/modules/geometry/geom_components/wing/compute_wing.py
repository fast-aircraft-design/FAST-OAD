"""
    Estimation of wing geometry
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

from fastoad.modules.geometry.geom_components.wing.components.compute_y_wing \
    import ComputeYWing
from fastoad.modules.geometry.geom_components.wing.components.compute_l1_l4 \
    import ComputeL1AndL4Wing
from fastoad.modules.geometry.geom_components.wing.components.compute_l2_l3 \
    import ComputeL2AndL3Wing
from fastoad.modules.geometry.geom_components.wing.components.compute_x_wing \
    import ComputeXWing
from fastoad.modules.geometry.geom_components.wing.components.compute_mac_wing \
    import ComputeMACWing
from fastoad.modules.geometry.geom_components.wing.components.compute_b_50 \
    import ComputeB50
from fastoad.modules.geometry.geom_components.wing.components.compute_sweep_wing \
    import ComputeSweepWing
from fastoad.modules.geometry.geom_components.wing.components.compute_toc_wing \
    import ComputeToCWing
from fastoad.modules.geometry.geom_components.wing.components.compute_wet_area_wing \
    import ComputeWetAreaWing
from fastoad.modules.geometry.geom_components.wing.components.compute_cl_alpha \
    import ComputeCLalpha
from fastoad.modules.geometry.geom_components.wing.components.compute_mfw \
    import ComputeMFW


class ComputeWingGeometry(Group):
    # TODO: Document equations. Cite sources
    """ Wing geometry estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_subsystem('y_wing', ComputeYWing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('l14_wing',
                           ComputeL1AndL4Wing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('l2l3_wing',
                           ComputeL2AndL3Wing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('x_wing', ComputeXWing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('mac_wing', ComputeMACWing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('b50_wing', ComputeB50(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('sweep_wing',
                           ComputeSweepWing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('toc_wing', ComputeToCWing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('wetarea_wing',
                           ComputeWetAreaWing(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('clapha_wing', ComputeCLalpha(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('mfw', ComputeMFW(deriv_method=deriv_method), promotes=['*'])
