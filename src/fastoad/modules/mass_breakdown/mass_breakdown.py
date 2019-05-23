"""
    FAST - Copyright (c) 2016 ONERA ISAE
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
from openmdao.solvers.linear.linear_block_gs import LinearBlockGS
from openmdao.solvers.nonlinear.nonlinear_block_gs import NonlinearBlockGS

from fastoad.modules.mass_breakdown.oew import OperatingEmptyWeight
from fastoad.modules.mass_breakdown.update_mlw_and_mzfw import UpdateMLWandMZFW


class MassBreakdown(Group):

    def initialize(self):
        self.options.declare('engine_location', types=float, default=1.0)
        self.options.declare('tail_type', types=float, default=0.)
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
        self.engine_location = self.options['engine_location']
        self.tail_type = self.options['tail_type']
        self.ac_type = self.options['ac_type']

        self.add_subsystem('oew', OperatingEmptyWeight(), promotes=['*'])
        self.add_subsystem('update_mzfw_and_mlw', UpdateMLWandMZFW(), promotes=['*'])

    def configure(self):
        # Solvers setup
        self.nonlinear_solver = NonlinearBlockGS()
        self.nonlinear_solver.options['iprint'] = 0
        self.nonlinear_solver.options['maxiter'] = 50
        # self.linear_solver = DirectSolver()
        self.linear_solver = LinearBlockGS()
        #        self.linear_solver = ScipyKrylov()
        self.linear_solver.options['iprint'] = 0
