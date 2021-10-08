"""Compressibility drag computation."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

from fastoad.module_management.service_registry import RegisterSubmodel
from ..constants import SERVICE_CD_COMPRESSIBILITY


@RegisterSubmodel(
    SERVICE_CD_COMPRESSIBILITY, "fastoad.submodel.aerodynamics.CD.compressibility.legacy"
)
class CdCompressibility(om.ExplicitComponent):
    """
    Computation of drag increment due to compressibility effects.

    Formula from §4.2.4 of :cite:`supaero:2014`. This formula can be used for aircraft
    before year 2000.

    Earlier aircraft have more optimized wing profiles that are expected to limit the
    compressibility drag below 2 drag counts. Until a better model can be provided, the
    variable `tuning:aerodynamics:aircraft:cruise:CD:compressibility:characteristic_mach_increment`
    allows to move the characteristic Mach number, thus moving the CD divergence to higher
    Mach numbers.
    """

    def setup(self):

        self.add_input("data:TLAR:cruise_mach", val=np.nan)
        self.add_input("data:aerodynamics:aircraft:cruise:CL", shape_by_conn=True, val=np.nan)
        self.add_input("data:geometry:wing:sweep_25", units="deg", val=np.nan)
        self.add_input("data:geometry:wing:thickness_ratio", val=np.nan)
        self.add_input("tuning:aerodynamics:aircraft:cruise:CD:compressibility:max_value", val=0.5)
        self.add_input(
            "tuning:aerodynamics:aircraft:cruise:CD:compressibility:characteristic_mach_increment",
            val=0.0,
        )
        self.add_output(
            "data:aerodynamics:aircraft:cruise:CD:compressibility",
            copy_shape="data:aerodynamics:aircraft:cruise:CL",
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        cl = inputs["data:aerodynamics:aircraft:cruise:CL"]
        m = inputs["data:TLAR:cruise_mach"]
        max_cd_comp = inputs["tuning:aerodynamics:aircraft:cruise:CD:compressibility:max_value"]
        delta_m_charac_0 = inputs[
            "tuning:aerodynamics:aircraft:cruise:CD:compressibility:characteristic_mach_increment"
        ]
        sweep_angle = inputs["data:geometry:wing:sweep_25"]
        thickness_ratio = inputs["data:geometry:wing:thickness_ratio"]

        # Computation of characteristic Mach for 28° sweep and 0.12 of relative thickness
        m_charac_comp_0 = (
            -0.5 * np.maximum(0.35, cl) ** 2
            + 0.35 * np.maximum(0.35, cl)
            + 0.765
            + delta_m_charac_0
        )

        # Computation of characteristic Mach for actual sweep angle and relative thickness
        m_charac_comp = (
            m_charac_comp_0 * np.cos(np.radians(28)) + 0.12 - thickness_ratio
        ) / np.cos(np.radians(sweep_angle))

        cd_comp = np.minimum(max_cd_comp, 0.002 * np.exp(42.58 * (m - m_charac_comp)))

        outputs["data:aerodynamics:aircraft:cruise:CD:compressibility"] = cd_comp
