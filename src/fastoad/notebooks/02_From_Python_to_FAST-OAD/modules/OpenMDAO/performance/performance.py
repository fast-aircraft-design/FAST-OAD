import openmdao.api as om

from .sub_components.compute_fuel_mass import ComputeFuelMass


class ComputePerformance(om.Group):
    def setup(self):

        self.add_subsystem(name="compute_fuel_mass", subsys=ComputeFuelMass(), promotes=["*"])
