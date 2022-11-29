from .geometry.geometry import ComputeGeometry
from .aerodynamics.aerodynamics import ComputeAerodynamics
from .mass.mass import ComputeMass
from .performance.performance import ComputePerformance
from .update_mtow.update_mtow import UpdateMTOW

import openmdao.api as om

import fastoad.api as oad


@oad.RegisterOpenMDAOSystem("tutorial.fast_oad.global")
class SizingLoopMTOW(om.Group):
    """
    Gather all the discipline module/groups into the main problem
    """

    def setup(self):

        self.add_subsystem(name="compute_geometry", subsys=ComputeGeometry(), promotes=["*"])
        self.add_subsystem(
            name="compute_aerodynamics", subsys=ComputeAerodynamics(), promotes=["*"]
        )
        self.add_subsystem(name="compute_mass", subsys=ComputeMass(), promotes=["*"])
        self.add_subsystem(name="compute_performance", subsys=ComputePerformance(), promotes=["*"])
        self.add_subsystem(name="update_mtow", subsys=UpdateMTOW(), promotes=["*"])
