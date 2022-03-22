from openmdao.api import Group

from ...OpenMDAO.performance.sub_components.compute_fuel_mass import ComputeFuelMass
from .sub_components.compute_new_mtow import ComputeNewMtow

import fastoad.api as oad


@oad.RegisterOpenMDAOSystem("tutorial.fast_oad.performance")
class ComputePerformance(Group):
    def setup(self):

        self.add_subsystem(name="compute_fuel_mass", subsys=ComputeFuelMass(), promotes=["*"])
        self.add_subsystem(name="compute_new_mtow", subsys=ComputeNewMtow(), promotes=["*"])
