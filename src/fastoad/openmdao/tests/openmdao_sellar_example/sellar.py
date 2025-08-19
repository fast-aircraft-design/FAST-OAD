"""Sellar openMDAO group"""

import openmdao.api as om

from fastoad._utils.sellar.sellar_base import BasicSellarModel, GenericSellarFactory, ISellarFactory

from .disc1 import Disc1
from .disc2 import Disc2
from .functions import FunctionF, FunctionG1, FunctionG2


class SellarModel(BasicSellarModel):
    """An OpenMDAO base component to encapsulate Sellar MDA"""

    def initialize(self):
        super().initialize()
        self.options["sellar_factory"] = GenericSellarFactory(
            disc1_class=Disc1,
            disc2_class=Disc2,
            f_class=FunctionF,
            g1_class=FunctionG1,
            g2_class=FunctionG2,
        )

    def setup(self):
        sellar_factory: ISellarFactory = self.options["sellar_factory"]

        indeps = self.add_subsystem("indeps", om.IndepVarComp(), promotes=["*"])
        indeps.add_output("x", 2)
        self.add_subsystem("disc1", sellar_factory.create_disc1(), promotes=["x", "z", "y2"])
        self.add_subsystem("disc2", sellar_factory.create_disc2(), promotes=["z", "y2"])
        self.add_subsystem(
            "objective",
            sellar_factory.create_objective_function(),
            promotes=["x", "z", "y2", "f"],
        )
        self.add_subsystem(
            "constraints", sellar_factory.create_constraints(), promotes=["y2", "g1", "g2"]
        )

        self.connect(
            "disc1.y1", ["disc2.y1", "objective.y1", "constraints.y1"]
        )  # Need for a non-promoted variable
