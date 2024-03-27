"""
Convenience classes to be used in OpenMDAO components
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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


class CycleGroup(om.Group):
    """
    Use this class as a base class if your model should contain a NonlinearBlockGS solver.

    This class defines standard options to control the solvers.

    Please be sure to call the `super()` method when using initialize() and setup()
    in the derived class.
    """

    def initialize(self):
        super().initialize()
        self.options.declare("use_inner_solver", types=bool, default=True)
        self.options.declare(
            "NLGS_options", types=dict, default={}, desc="options for NonlinearBlockGS"
        )
        self.options.declare("DS_options", types=dict, default={}, desc="options for DirectSolver")

    def setup(self):
        if self.options["use_inner_solver"]:
            self.nonlinear_solver = om.NonlinearBlockGS(**self.options["NLGS_options"])
            self.linear_solver = om.DirectSolver(**self.options["DS_options"])
        super().setup()
