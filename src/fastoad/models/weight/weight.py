"""
Weight computation (mass and CG)
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

from fastoad.models.options import OpenMdaoOptionDispatcherGroup, AIRCRAFT_TYPE_OPTION
from fastoad.models.weight.cg.cg import CG
from fastoad.models.weight.mass_breakdown import MassBreakdown


class Weight(OpenMdaoOptionDispatcherGroup):
    """
    Computes masses and Centers of Gravity for each part of the empty operating aircraft, among
    these 5 categories:
    airframe, propulsion, systems, furniture, crew

    This model uses MTOW as an input, as it allows to size some elements, but resulting OWE do
    not aim at being consistent with MTOW.

    Consistency between OWE and MTOW can be achieved by cycling with a model that computes MTOW
    from OWE, which should come from a mission computation that will assess needed block fuel.
    """

    def initialize(self):
        self.options.declare(AIRCRAFT_TYPE_OPTION, types=float, default=2.0)

    def setup(self):
        self.add_subsystem("cg", CG(), promotes=["*"])
        self.add_subsystem("mass_breakdown", MassBreakdown(), promotes=["*"])
