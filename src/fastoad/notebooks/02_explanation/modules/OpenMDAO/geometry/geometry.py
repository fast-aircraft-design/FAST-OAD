import openmdao.api as om

from .sub_components.compute_wing_area import ComputeWingArea


class ComputeGeometry(om.Group):
    def setup(self):

        self.add_subsystem(name="compute_wing_area", subsys=ComputeWingArea(), promotes=["*"])
