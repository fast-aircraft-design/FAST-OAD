"""Sellar indeps"""

import openmdao.api as om

from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("configuration_test.sellar.indeps")
class Indeps(om.Group):
    def setup(self):
        # System variables
        comp = om.IndepVarComp()
        comp.add_output("system:x", val=2)

        self.add_subsystem("indeps", comp, promotes=["*"])
