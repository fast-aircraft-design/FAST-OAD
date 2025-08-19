"""
Computation of beam linear weight.
"""

import numpy as np
import openmdao.api as om

import fastoad.api as oad


@oad.RegisterOpenMDAOSystem("tutorial.beam_problem.weight")
class LinearWeight(om.ExplicitComponent):
    """
    Computes beam linear weight given its dimensions.
    """

    def setup(self):
        self.add_input("data:geometry:l", val=np.nan, units="m")
        self.add_input("data:geometry:h", val=np.nan, units="m")
        self.add_input("data:material:density", val=np.nan, units="kg/m**3")

        self.add_output("data:weight:linear_weight", val=10.0, units="N/m")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        length = inputs["data:geometry:l"]
        height = inputs["data:geometry:h"]
        rho = inputs["data:material:density"]

        outputs["data:weight:linear_weight"] = length * height * rho * 9.81
