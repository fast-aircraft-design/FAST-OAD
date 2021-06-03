"""The place for module-level constants."""
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

from aenum import Enum

# Services
SERVICE_OPENMDAO_SYSTEM = "fast.openmdao.system"
SERVICE_PROPULSION_WRAPPER = "fastoad.wrapper.propulsion"

# Properties for RegisterOpenMDAOSystem
OPTION_PROPERTY_NAME = "OPTIONS"
DESCRIPTION_PROPERTY_NAME = "DESCRIPTION"
DOMAIN_PROPERTY_NAME = "DOMAIN"


# Definition of model domains
class ModelDomain(Enum):
    """
    Enumeration of model domains.
    """

    GEOMETRY = "Geometry"
    AERODYNAMICS = "Aerodynamics"
    HANDLING_QUALITIES = "Handling Qualities"
    WEIGHT = "Weight"
    PERFORMANCE = "Performance"
    PROPULSION = "Propulsion"
    OTHER = "Other"
    UNSPECIFIED = "Unspecified"
