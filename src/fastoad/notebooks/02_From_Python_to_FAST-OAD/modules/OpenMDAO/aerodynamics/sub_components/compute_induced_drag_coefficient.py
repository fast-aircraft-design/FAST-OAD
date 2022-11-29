import numpy as np

import openmdao.api as om


class ComputeInducedDragCoefficient(om.ExplicitComponent):
    """
    Computes the induced drag coefficient based on the aspect ratio
    """

    def setup(self):

        # Defining the input(s)

        self.add_input(name="aspect_ratio", val=np.nan)

        # Defining the output(s)

        self.add_output(name="induced_drag_coefficient")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        # Assigning the input to local variable for clarity
        aspect_ratio = inputs["aspect_ratio"]

        # Computation of the Oswald efficiency factor
        e = 1.78 * (1.0 - 0.045 * aspect_ratio ** 0.68) - 0.64

        # Computation of the lift induced drag coefficient
        k = 1.0 / (np.pi * aspect_ratio * e)

        outputs["induced_drag_coefficient"] = k
