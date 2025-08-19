"""The place for module-level constants."""

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
    LOADS = "Loads"
    OTHER = "Other"
    UNSPECIFIED = "Unspecified"
