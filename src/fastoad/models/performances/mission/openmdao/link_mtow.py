"""
OpenMDAO component for computation of sizing mission.
"""

import openmdao.api as om

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("fastoad.mass_performances.compute_MTOW", domain=ModelDomain.OTHER)
class ComputeMTOW(om.AddSubtractComp):
    """
    Computes MTOW from OWE, design payload and consumed fuel in sizing mission.
    """

    def setup(self):
        self.add_equation(
            "data:weight:aircraft:MTOW",
            [
                "data:weight:aircraft:OWE",
                "data:weight:aircraft:payload",
                "data:weight:aircraft:sizing_onboard_fuel_at_input_weight",
            ],
            units="kg",
        )
