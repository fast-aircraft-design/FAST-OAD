import numpy as np

from openmdao.api import ExplicitComponent


class ComputeOwe(ExplicitComponent):
    """
    Computes the aircraft structural mass based on its MTOW and wing mass
    """

    def setup(self):

        pass
