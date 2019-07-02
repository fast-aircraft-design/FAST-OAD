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

# from fast.Aerodynamics.components.compute_max_cl_clean import ComputeMaxClClean
from fastoad.modules.aerodynamics.components.prepare_2d_run import Prepare2dRun
from fastoad.modules.aerodynamics.external.xfoil import XfoilPolar


class Aerodynamics2d(Group):

    def setup(self):
        self.add_subsystem('prepare_2d_run', Prepare2dRun(), promotes=['*'])
        self.add_subsystem('xfoil_run', XfoilPolar(), promotes=['*'])
