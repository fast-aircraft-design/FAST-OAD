import numpy as np

import openmdao.api as om


class ComputeOwe(om.ExplicitComponent):
    """
    Computes the aircraft structural mass based on its MTOW and wing mass
    """

    def setup(self):

        pass
