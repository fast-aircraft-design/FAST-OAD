"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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

import openmdao.api as om

from fastoad.modules.geometry.cg_components.compute_cg_control_surfaces import \
    ComputeControlSurfacesCG
from fastoad.modules.geometry.cg_components.compute_cg_others import ComputeOthersCG
from fastoad.modules.geometry.cg_components.compute_cg_tanks import ComputeTanksCG
from fastoad.modules.geometry.cg_components.compute_cg_wing import ComputeWingCG
from fastoad.modules.geometry.cg_components.compute_global_cg import ComputeGlobalCG
from fastoad.modules.geometry.geom_components.compute_total_area import ComputeTotalArea
from fastoad.modules.geometry.geom_components.ht import ComputeHorizontalTailGeometry
from fastoad.modules.geometry.geom_components.update_mlg import UpdateMLG
from fastoad.modules.geometry.geom_components.vt import ComputeVerticalTailGeometry
from fastoad.modules.options import TAIL_TYPE_OPTION, \
    AIRCRAFT_FAMILY_OPTION, OpenMdaoOptionDispatcherGroup


class GetCG(OpenMdaoOptionDispatcherGroup):
    """ Model that computes the global center of gravity """

    def initialize(self):
        self.options.declare(TAIL_TYPE_OPTION, types=float, default=0.0)
        self.options.declare(AIRCRAFT_FAMILY_OPTION, types=float, default=1.0)

    def setup(self):
        self.add_subsystem('compute_ht', ComputeHorizontalTailGeometry(), promotes=['*'])
        self.add_subsystem('compute_vt', ComputeVerticalTailGeometry(), promotes=['*'])
        self.add_subsystem('compute_total_area', ComputeTotalArea(), promotes=['*'])
        self.add_subsystem('compute_cg_wing', ComputeWingCG(), promotes=['*'])
        self.add_subsystem('compute_cg_control_surface', ComputeControlSurfacesCG(), promotes=['*'])
        self.add_subsystem('compute_cg_tanks', ComputeTanksCG(), promotes=['*'])
        self.add_subsystem('compute_cg_others', ComputeOthersCG(), promotes=['*'])
        self.add_subsystem('compute_cg', ComputeGlobalCG(), promotes=['*'])
        self.add_subsystem('update_mlg', UpdateMLG(), promotes=['*'])

        # Solvers setup
        self.nonlinear_solver = om.NonlinearBlockGS()
        self.nonlinear_solver.options['iprint'] = 0
        self.nonlinear_solver.options['maxiter'] = 100
        self.linear_solver = om.LinearBlockGS()
        self.linear_solver.options['iprint'] = 0
