import openmdao.api as om

import fastoad.api as oad
from ...OpenMDAO.mass.sub_components.compute_owe import ComputeOwe
from ...OpenMDAO.mass.sub_components.compute_wing_mass import ComputeWingMass


@oad.RegisterOpenMDAOSystem("tutorial.fast_oad.mass")
class ComputeMass(om.Group):
    def setup(self):
        self.add_subsystem(name="compute_wing_mass", subsys=ComputeWingMass(), promotes=["*"])
        self.add_subsystem(name="compute_owe", subsys=ComputeOwe(), promotes=["*"])
