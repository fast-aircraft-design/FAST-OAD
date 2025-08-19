"""Sellar discipline 2"""

import openmdao.api as om


class BasicDisc2(om.ExplicitComponent):
    """An OpenMDAO component to encapsulate Disc2 discipline"""

    def setup(self):
        self.add_input("z", val=[5.0, 2.0])
        self.add_input("y1", val=1.0)

        self.add_output("y2", val=1.0)

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    # pylint: disable=invalid-name
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """
        Evaluates the equation
        y2 = y1**(.5) + z1 + z2
        """

        z1 = inputs["z"][0]
        z2 = inputs["z"][1]
        y1 = inputs["y1"]

        # Note: this may cause some issues. However, y1 is constrained to be
        # above 3.16, so lets just let it converge, and the optimizer will
        # throw it out
        if y1.real < 0.0:
            y1 *= -1

        outputs["y2"] = y1**0.5 + z1 + z2
