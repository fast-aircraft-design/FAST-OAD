"""Sellar functions"""

from math import exp

import openmdao.api as om


class BasicFunctionF(om.ExplicitComponent):
    """An OpenMDAO component to encapsulate Functions discipline"""

    def setup(self):
        self.add_input("x", val=2.0)
        self.add_input("z", val=[5.0, 2.0])
        self.add_input("y1", val=1.0)
        self.add_input("y2", val=1.0)

        self.add_output("f", val=1.0)

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """Functions computation"""

        z2 = inputs["z"][1]
        x1 = inputs["x"].item()
        y1 = inputs["y1"].item()
        y2 = inputs["y2"].item()

        outputs["f"] = x1**2 + z2 + y1 + exp(-y2)
