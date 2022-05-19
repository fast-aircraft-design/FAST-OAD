import openmdao.api as om

from ...OpenMDAO.performance.sub_components.compute_fuel_mass import ComputeFuelMass

import fastoad.api as oad


@oad.RegisterOpenMDAOSystem("tutorial.fast_oad.performance")
class ComputePerformance(om.Group):
    def setup(self):

        self.add_subsystem(name="compute_fuel_mass", subsys=ComputeFuelMass(), promotes=["*"])
