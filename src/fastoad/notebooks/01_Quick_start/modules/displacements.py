"""
Computation of needed beam section for a target deflection.
"""

import numpy as np
import openmdao.api as om

import fastoad.api as oad


@oad.RegisterOpenMDAOSystem("tutorial.beam_problem.disp")
class Displacements(om.ExplicitComponent):
    """
    Computes needed beam section second moment of area given a target deflection, force and
    material properties.
    """

    def setup(self):
        self.add_input("data:geometry:L", val=np.nan, units="m")
        self.add_input("data:material:E", val=np.nan, units="Pa")
        self.add_input("data:forces:F", val=np.nan, units="N")
        self.add_input("data:weight:linear_weight", val=np.nan, units="N/m")
        self.add_input("data:displacements:target", val=np.nan, units="m")

        self.add_output("data:geometry:Ixx", val=1e-5, units="m**4")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        L = inputs["data:geometry:L"]
        E = inputs["data:material:E"]
        F = inputs["data:forces:F"]
        w = inputs["data:weight:linear_weight"]
        v = inputs["data:displacements:target"]

        outputs["data:geometry:Ixx"] = L**3 * (F / 3 - w * L / 8) / (E * v)
