from openmdao.api import Group

from ...OpenMDAO.geometry.sub_components.compute_wing_area import ComputeWingArea

import fastoad.api as oad


@oad.RegisterOpenMDAOSystem("tutorial.fast_oad.geometry")
class ComputeGeometry(Group):
    def setup(self):

        self.add_subsystem(name="compute_wing_area", subsys=ComputeWingArea(), promotes=["*"])
