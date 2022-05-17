import openmdao.api as om

from .sub_components.compute_profile_drag import ComputeProfileDrag
from .sub_components.compute_induced_drag_coefficient import ComputeInducedDragCoefficient
from .sub_components.compute_lift_to_drag_ratio import ComputeLiftToDragRatio


class ComputeAerodynamics(om.Group):
    def setup(self):

        self.add_subsystem(name="compute_profile_drag", subsys=ComputeProfileDrag(), promotes=["*"])
        self.add_subsystem(
            name="compute_induced_drag", subsys=ComputeInducedDragCoefficient(), promotes=["*"]
        )
        self.add_subsystem(
            name="compute_lift_to_drag", subsys=ComputeLiftToDragRatio(), promotes=["*"]
        )
