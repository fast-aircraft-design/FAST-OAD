import numpy as np
import scipy.constants as sc

import openmdao.api as om


class ComputeWingMass(om.ExplicitComponent):
    """
    Computes the wing mass based on the MTOW, its area and aspect ratio
    """

    def setup(self):

        # Defining the input(s)

        self.add_input(name="wing_area", units="ft**2", val=np.nan)
        # Notice that here we ask for the wing area in sq. ft as it is the unit we need for the
        # formula, so we won't need to convert the wing area in the proper unit
        self.add_input(name="mtow", units="lbm", val=np.nan)
        # Same for the MTOW
        self.add_input(name="aspect_ratio", val=np.nan)

        # Defining the output(s)

        self.add_output(name="wing_mass", units="lbm")
        # Same situation here, the formula outputs in lbm but if we later want to use it in kg,
        # we will just have to ask for units="kg" and OpenMDAO automatically handles the conversion

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        # Assigning the input to local variable for clarity
        wing_area = inputs["wing_area"]
        aspect_ratio = inputs["aspect_ratio"]
        mtow = inputs["mtow"]

        # Let's now apply the formula
        wing_mass = (
            96.948
            * (
                (5.7 * mtow / 1.0e5) ** 0.65
                * aspect_ratio ** 0.57
                * (wing_area / 100.0) ** 0.61
                * 2.5
            )
            ** 0.993
        )

        outputs["wing_mass"] = wing_mass
