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
from fastoad.models.aerodynamics.components.cd_compressibility import CdCompressibility
from fastoad.models.aerodynamics.components.cd_trim import CdTrim
from fastoad.models.aerodynamics.components.compute_polar import ComputePolar
from fastoad.models.aerodynamics.components.compute_reynolds import ComputeReynolds
from fastoad.models.aerodynamics.components.initialize_cl import InitializeClPolar
from fastoad.models.aerodynamics.components.oswald import OswaldCoefficient
from openmdao.core.group import Group


class AerodynamicsHighSpeed(Group):
    """
    Computes aerodynamic polar of the aircraft in cruise conditions.

    Drag contributions of each part of the aircraft are computed though analytical
    models.
    """

    def setup(self):
        self.add_subsystem("compute_oswald_coeff", OswaldCoefficient(), promotes=["*"])
        self.add_subsystem("comp_re", ComputeReynolds(), promotes=["*"])
        self.add_subsystem("initialize_cl", InitializeClPolar(), promotes=["*"])
        self.add_subsystem("cd0_wing", Cd0Wing(), promotes=["*"])
        self.add_subsystem("cd0_fuselage", Cd0Fuselage(), promotes=["*"])
        self.add_subsystem("cd0_ht", Cd0HorizontalTail(), promotes=["*"])
        self.add_subsystem("cd0_vt", Cd0VerticalTail(), promotes=["*"])
        self.add_subsystem("cd0_nac_pylons", Cd0NacelleAndPylons(), promotes=["*"])
        self.add_subsystem("cd0_total", Cd0Total(), promotes=["*"])
        self.add_subsystem("cd_comp", CdCompressibility(), promotes=["*"])
        self.add_subsystem("cd_trim", CdTrim(), promotes=["*"])
        self.add_subsystem("get_polar", ComputePolar(), promotes=["*"])
