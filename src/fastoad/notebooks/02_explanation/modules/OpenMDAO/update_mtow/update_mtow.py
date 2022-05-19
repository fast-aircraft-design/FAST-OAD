import numpy as np

import openmdao.api as om


class UpdateMTOW(om.ExplicitComponent):
    """
    Computes new mtow based on the mission fuel and structural weight from previous iteration
    """

    def setup(self):

        # Defining the input(s)

        self.add_input(name="owe", units="kg", val=np.nan)
        self.add_input(name="payload", units="kg", val=np.nan)
        self.add_input(name="mission_fuel", units="kg", val=np.nan)

        # Defining the output(s)

        self.add_output(name="mtow", units="kg")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        # Assigning the input to local variable for clarity
        owe = inputs["owe"]
        payload = inputs["payload"]
        mission_fuel = inputs["mission_fuel"]

        # Let's simply add the weight we computed
        mtow_new = owe + payload + mission_fuel

        outputs["mtow"] = mtow_new
