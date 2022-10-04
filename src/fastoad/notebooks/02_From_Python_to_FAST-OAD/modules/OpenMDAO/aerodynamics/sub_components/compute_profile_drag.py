import numpy as np

import openmdao.api as om


class ComputeProfileDrag(om.ExplicitComponent):
    """
    Computes the profile drag of the aircraft based on the wing area
    """

    def setup(self):

        # Defining the input(s)

        self.add_input(name="wing_area", units="m**2", val=np.nan)

        # Defining the output(s)

        self.add_output(name="profile_drag_coefficient")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        # Assigning the input to local variable for clarity
        wing_area = inputs["wing_area"]

        # Wet area of the aircraft without the wings
        wing_area_ref = 13.50

        # Profile drag coefficient of the aircraft without the wings
        cd0_other = 0.022

        # Constant linking the wing profile drag to its wet area, and by extension, its reference area
        c = 0.0004

        # Computation of the profile drag
        cd0 = cd0_other * wing_area_ref / wing_area + c

        outputs["profile_drag_coefficient"] = cd0
