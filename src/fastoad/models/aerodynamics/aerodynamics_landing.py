"""
Aero computation for landing phase
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

import numpy as np
import openmdao.api as om

from fastoad.models.aerodynamics.components.compute_max_cl_landing import ComputeMaxClLanding
from fastoad.models.aerodynamics.components.high_lift_aero import ComputeDeltaHighLift
from fastoad.models.aerodynamics.external.xfoil import XfoilPolar
from fastoad.models.aerodynamics.external.xfoil.xfoil_polar import OPTION_XFOIL_EXE_PATH
from fastoad.models.options import OpenMdaoOptionDispatcherGroup
from fastoad.utils.physics import Atmosphere


class AerodynamicsLanding(OpenMdaoOptionDispatcherGroup):
    """
    Computes maximum CL of the aircraft in landing conditions.

    Maximum CL without high-lift is computed using XFoil (or provided as input if option use_xfoil
    is set to False).
    Contribution of high-lift devices is modelled according to their geometry (span and chord ratio) and
    their deflection angles.

    Options:
      - use_xfoil:
         - if True, maximum CL without high-lift aerodynamics:aircraft:landing:CL_max_clean is
           computed using XFOIL
         - if False, aerodynamics:aircraft:landing:CL_max_clean must be provided as input (but
           process is faster)
      - alpha_min, alpha_max:
         - used if use_xfoil is True. Sets the alpha range that is explored to find maximum CL
           without high-lift
      - xfoil_exe_path:
         - the path to the XFOIL executable. Needed for non-Windows OS.
    """

    def initialize(self):
        self.options.declare("use_xfoil", default=True, types=bool)
        self.options.declare("xfoil_alpha_min", default=15.0, types=float)
        self.options.declare("xfoil_alpha_max", default=25.0, types=float)
        self.options.declare("xfoil_iter_limit", default=20, types=int)
        self.options.declare(OPTION_XFOIL_EXE_PATH, default="", types=str, allow_none=True)

    def setup(self):
        self.add_subsystem("mach_reynolds", ComputeMachReynolds(), promotes=["*"])
        if self.options["use_xfoil"]:
            start = self.options["xfoil_alpha_min"]
            end = self.options["xfoil_alpha_max"]
            iter_limit = self.options["xfoil_iter_limit"]
            self.add_subsystem(
                "xfoil_run",
                XfoilPolar(alpha_start=start, alpha_end=end, iter_limit=iter_limit),
                promotes=["data:geometry:wing:sweep_25", "data:geometry:wing:thickness_ratio"],
            )
        self.add_subsystem(
            "delta_cl_landing", ComputeDeltaHighLift(landing_flag=True), promotes=["*"]
        )
        self.add_subsystem("compute_max_cl_landing", ComputeMaxClLanding(), promotes=["*"])

        if self.options["use_xfoil"]:
            self.connect("data:aerodynamics:aircraft:landing:mach", "xfoil_run.xfoil:mach")
            self.connect("data:aerodynamics:aircraft:landing:reynolds", "xfoil_run.xfoil:reynolds")
            self.connect(
                "xfoil_run.xfoil:CL_max_clean", "data:aerodynamics:aircraft:landing:CL_max_clean"
            )


class ComputeMachReynolds(om.ExplicitComponent):
    def setup(self):
        self.add_input("data:geometry:wing:MAC:length", val=np.nan, units="m")
        self.add_input("data:TLAR:approach_speed", val=np.nan, units="m/s")
        self.add_output("data:aerodynamics:aircraft:landing:mach")
        self.add_output("data:aerodynamics:aircraft:landing:reynolds")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        l0_wing = inputs["data:geometry:wing:MAC:length"]
        speed = inputs["data:TLAR:approach_speed"]

        atm = Atmosphere(0.0, 15.0)
        mach = speed / atm.speed_of_sound
        reynolds = atm.get_unitary_reynolds(mach) * l0_wing

        outputs["data:aerodynamics:aircraft:landing:mach"] = mach
        outputs["data:aerodynamics:aircraft:landing:reynolds"] = reynolds
