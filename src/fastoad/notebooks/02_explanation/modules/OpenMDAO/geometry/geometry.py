from openmdao.api import Group

from .sub_components.compute_wing_area import ComputeWingArea


class ComputeGeometry(Group):
    def setup(self):

        self.add_subsystem(name="compute_wing_area", subsys=ComputeWingArea(), promotes=["*"])
