import openmdao.api as om

import fastoad.api as oad
from ...OpenMDAO.geometry.sub_components.compute_wing_area import ComputeWingArea


@oad.RegisterOpenMDAOSystem("tutorial.fast_oad.geometry")
class ComputeGeometry(om.Group):
    def setup(self):
        self.add_subsystem(name="compute_wing_area", subsys=ComputeWingArea(), promotes=["*"])
