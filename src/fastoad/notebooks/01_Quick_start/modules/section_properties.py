"""
Computation of section properties.
"""

import numpy as np
import openmdao.api as om

import fastoad.api as oad


@oad.RegisterOpenMDAOSystem("tutorial.beam_problem.geometry")
class RectangularSection(om.ExplicitComponent):
    """
    Computes section properties of a beam given width and height.
    """

    def setup(self):
        self.add_input("data:geometry:l", val=np.nan, units="m")
        self.add_input("data:geometry:Ixx", val=np.nan, units="m**4")
        self.add_output("data:geometry:h", val=0.01, units="m")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        length = inputs["data:geometry:l"]
        I_xx = inputs["data:geometry:Ixx"]

        outputs["data:geometry:h"] = (12 * I_xx / length) ** (1 / 3)
