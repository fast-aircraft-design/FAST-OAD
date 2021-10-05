"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""
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

import openmdao.api as om

from fastoad.models.constants import CABIN_SIZING_OPTION
from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem, RegisterSubmodel
from .compute_aero_center import ComputeAeroCenter
from .geom_components import ComputeTotalArea
from .geom_components.vt import ComputeVerticalTailGeometry
from .geom_components.wing.compute_wing import ComputeWingGeometry

SERVICE_FUSELAGE_GEOMETRY_BASIC = "service.geometry.fuselage.basic"
SERVICE_FUSELAGE_GEOMETRY_WITH_CABIN_SIZING = "service.geometry.fuselage.with_cabin_sizing"
SERVICE_HORIZONTAL_TAIL_GEOMETRY = "service.geometry.horizontal_tail"
SERVICE_NACELLE_PYLON_GEOMETRY = "service.geometry.nacelle_and_pylon"


@RegisterOpenMDAOSystem("fastoad.geometry.legacy", domain=ModelDomain.GEOMETRY)
class Geometry(om.Group):
    """
    Computes geometric characteristics of the (tube-wing) aircraft:
      - fuselage size can be computed from payload requirements
      - wing dimensions are computed from global parameters (area, taper ratio...)
      - tail planes are dimensioned from HQ requirements
    """

    def initialize(self):
        self.options.declare(
            CABIN_SIZING_OPTION,
            types=bool,
            default=True,
            desc="If True, fuselage dimensions will be computed from cabin specifications."
            "\nIf False, fuselage dimensions will be input data.",
        )

    def setup(self):

        if self.options[CABIN_SIZING_OPTION]:
            self.add_subsystem(
                "compute_fuselage",
                RegisterSubmodel.get_submodel(SERVICE_FUSELAGE_GEOMETRY_WITH_CABIN_SIZING),
                promotes=["*"],
            )
        else:
            self.add_subsystem(
                "compute_fuselage",
                RegisterSubmodel.get_submodel(SERVICE_FUSELAGE_GEOMETRY_BASIC),
                promotes=["*"],
            )

        self.add_subsystem("compute_wing", ComputeWingGeometry(), promotes=["*"])
        self.add_subsystem(
            "compute_engine_nacelle",
            RegisterSubmodel.get_submodel(SERVICE_NACELLE_PYLON_GEOMETRY),
            promotes=["*"],
        )
        self.add_subsystem(
            "compute_ht",
            RegisterSubmodel.get_submodel(SERVICE_HORIZONTAL_TAIL_GEOMETRY),
            promotes=["*"],
        )
        self.add_subsystem("compute_vt", ComputeVerticalTailGeometry(), promotes=["*"])
        self.add_subsystem("compute_total_area", ComputeTotalArea(), promotes=["*"])
        self.add_subsystem("compute_aero_center", ComputeAeroCenter(), promotes=["*"])
