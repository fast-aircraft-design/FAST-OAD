import openmdao.api as om

import fastoad.api as oad
from ...OpenMDAO.aerodynamics.sub_components.compute_induced_drag_coefficient import (
    ComputeInducedDragCoefficient,
)
from ...OpenMDAO.aerodynamics.sub_components.compute_lift_to_drag_ratio import (
    ComputeLiftToDragRatio,
)
from ...OpenMDAO.aerodynamics.sub_components.compute_profile_drag import ComputeProfileDrag


@oad.RegisterOpenMDAOSystem("tutorial.fast_oad.aerodynamics")
class ComputeAerodynamics(om.Group):
    def setup(self):
        self.add_subsystem(name="compute_profile_drag", subsys=ComputeProfileDrag(), promotes=["*"])
        self.add_subsystem(
            name="compute_induced_drag", subsys=ComputeInducedDragCoefficient(), promotes=["*"]
        )
        self.add_subsystem(
            name="compute_lift_to_drag", subsys=ComputeLiftToDragRatio(), promotes=["*"]
        )
