import openmdao.api as om

import fastoad.api as oad

from ...OpenMDAO.performance.sub_components.compute_fuel_mass import ComputeFuelMass


@oad.RegisterOpenMDAOSystem("tutorial.fast_oad.performance")
class ComputePerformance(om.Group):
    def setup(self):
        self.add_subsystem(name="compute_fuel_mass", subsys=ComputeFuelMass(), promotes=["*"])
