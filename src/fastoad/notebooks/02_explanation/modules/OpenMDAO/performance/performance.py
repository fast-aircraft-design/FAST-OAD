from openmdao.api import Group

from .sub_components.compute_fuel_mass import ComputeFuelMass
from .sub_components.compute_new_mtow import ComputeNewMtow


class ComputePerformance(Group):
    def setup(self):

        self.add_subsystem(name="compute_fuel_mass", subsys=ComputeFuelMass(), promotes=["*"])
        self.add_subsystem(name="compute_new_mtow", subsys=ComputeNewMtow(), promotes=["*"])
