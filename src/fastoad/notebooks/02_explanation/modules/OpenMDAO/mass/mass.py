from openmdao.api import Group

from .sub_components.compute_wing_mass import ComputeWingMass
from .sub_components.compute_owe import ComputeOwe


class ComputeMass(Group):
    def setup(self):

        self.add_subsystem(name="compute_wing_mass", subsys=ComputeWingMass(), promotes=["*"])
        self.add_subsystem(name="compute_owe", subsys=ComputeOwe(), promotes=["*"])
