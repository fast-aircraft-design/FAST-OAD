"""Sellar discipline 1"""

import openmdao.api as om

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem(
    "module_management_test.sellar.disc1", desc="some text", domain=ModelDomain.OTHER
)
class BasicDisc1(om.ExplicitComponent):
    """An OpenMDAO component to encapsulate Disc1 discipline"""

    def setup(self):
        self.add_input("x", val=2.0)
        self.add_input("z", val=[5.0, 2.0])
        self.add_input("y2", val=1.0)

        self.add_output("y1", val=1.0)

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    # pylint: disable=invalid-name
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """
        Evaluates the equation
        y1 = z1**2 + z2 + x1 - 0.2*y2
        """
        z1 = inputs["z"][0]
        z2 = inputs["z"][1]
        x1 = inputs["x"]
        y2 = inputs["y2"]

        outputs["y1"] = z1**2 + z2 + x1 - 0.2 * y2
