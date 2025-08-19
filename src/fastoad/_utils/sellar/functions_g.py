"""Sellar functions"""

import openmdao.api as om


class BasicFunctionG1(om.ExplicitComponent):
    """An OpenMDAO component to encapsulate Functions discipline"""

    def setup(self):
        self.add_input("y1", val=1.0)
        self.add_output("g1", val=1.0)

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """Functions computation"""
        y1 = inputs["y1"]
        outputs["g1"] = 3.16 - y1


class BasicFunctionG2(om.ExplicitComponent):
    """An OpenMDAO component to encapsulate Functions discipline"""

    def setup(self):
        self.add_input("y2", val=1.0, desc="")
        self.add_output("g2", val=1.0, desc="")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """Functions computation"""
        y2 = inputs["y2"]
        outputs["g2"] = y2 - 24.0
