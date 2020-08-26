"""
    FAST - Copyright (c) 2016 ONERA ISAE
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

from fastoad.models.aerodynamics.components.cd0_fuselage import Cd0Fuselage
from fastoad.models.aerodynamics.components.cd0_ht import Cd0HorizontalTail
from fastoad.models.aerodynamics.components.cd0_nacelle_pylons import Cd0NacelleAndPylons
from fastoad.models.aerodynamics.components.cd0_total import Cd0Total
from fastoad.models.aerodynamics.components.cd0_vt import Cd0VerticalTail
from fastoad.models.aerodynamics.components.cd0_wing import Cd0Wing
from fastoad.models.aerodynamics.components.cd_trim import CdTrim
from fastoad.models.aerodynamics.components.compute_low_speed_aero import (
    ComputeAerodynamicsLowSpeed,
)
from fastoad.models.aerodynamics.components.compute_polar import ComputePolar, PolarType
from fastoad.models.aerodynamics.components.compute_reynolds import ComputeReynolds
from fastoad.models.aerodynamics.components.initialize_cl import InitializeClPolar
from fastoad.models.aerodynamics.components.oswald import OswaldCoefficient
from openmdao.core.group import Group
from openmdao.core.indepvarcomp import IndepVarComp


class AerodynamicsLowSpeed(Group):
    """
    Models for low speed aerodynamics
    """

    def setup(self):
        self.add_subsystem("compute_low_speed_aero", ComputeAerodynamicsLowSpeed(), promotes=["*"])
        ivc = IndepVarComp("data:aerodynamics:aircraft:takeoff:mach", val=0.2)
        self.add_subsystem("mach_low_speed", ivc, promotes=["*"])
        self.add_subsystem(
            "compute_oswald_coeff", OswaldCoefficient(low_speed_aero=True), promotes=["*"]
        )
        self.add_subsystem("comp_re", ComputeReynolds(low_speed_aero=True), promotes=["*"])
        self.add_subsystem("initialize_cl", InitializeClPolar(low_speed_aero=True), promotes=["*"])
        self.add_subsystem("cd0_wing", Cd0Wing(low_speed_aero=True), promotes=["*"])
        self.add_subsystem("cd0_fuselage", Cd0Fuselage(low_speed_aero=True), promotes=["*"])
        self.add_subsystem("cd0_ht", Cd0HorizontalTail(low_speed_aero=True), promotes=["*"])
        self.add_subsystem("cd0_vt", Cd0VerticalTail(low_speed_aero=True), promotes=["*"])
        self.add_subsystem(
            "cd0_nac_pylons", Cd0NacelleAndPylons(low_speed_aero=True), promotes=["*"]
        )
        self.add_subsystem("cd0_total", Cd0Total(low_speed_aero=True), promotes=["*"])
        self.add_subsystem("cd_trim", CdTrim(low_speed_aero=True), promotes=["*"])
        self.add_subsystem("get_polar", ComputePolar(type=PolarType.LOW_SPEED), promotes=["*"])
