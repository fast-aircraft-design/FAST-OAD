import numpy as np
import openmdao.api as om


class Disc1(om.ExplicitComponent):
    """ An OpenMDAO component to encapsulate Disc1 discipline and test """

    def setup(self):
        self.add_input(
            "data:geometry:variable_1", val=np.nan, desc=""
        )  # NaN as default for testing connexion check
        self.add_input(
            "data:geometry:variable_2", val=[5, 2], desc="", units="m**2"
        )  # for testing non-None units
        self.add_input("data:geometry:variable_3", val=1.0, desc="")

        self.add_output("data:geometry:variable_4", val=1.0, desc="")
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """
        Evaluates a simple equation
        """
        x1 = inputs["data:geometry:variable_1"][0]
        x21 = inputs["data:geometry:variable_2"][0]
        x22 = inputs["data:geometry:variable_2"][1]
        x3 = inputs["data:geometry:variable_3"][0]

        outputs["data:geometry:variable_4"] = x1 + x21 * x22 - x3


class Disc2(om.Group):
    """ An OpenMDAO component to encapsulate Disc1 and an IVC """

    def setup(self):
        ivc = om.IndepVarComp()
        ivc.add_output("data:geometry:variable_1", val=6.0)
        self.add_subsystem("ivc1", ivc, promotes=["*"])
        self.add_subsystem("disc1", Disc1(), promotes=["*"])
