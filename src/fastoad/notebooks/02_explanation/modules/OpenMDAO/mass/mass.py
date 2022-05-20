import openmdao.api as om

from .sub_components.compute_wing_mass import ComputeWingMass
from .sub_components.compute_owe_exercise import ComputeOweExercise
from .sub_components.compute_owe import ComputeOwe


class ComputeMassCorrect(om.Group):
    def setup(self):

        self.add_subsystem(name="compute_wing_mass", subsys=ComputeWingMass(), promotes=["*"])
        self.add_subsystem(name="compute_owe", subsys=ComputeOwe(), promotes=["*"])


class ComputeMassExercise(om.Group):
    def setup(self):

        self.add_subsystem(name="compute_wing_mass", subsys=ComputeWingMass(), promotes=["*"])
        self.add_subsystem(name="compute_owe", subsys=ComputeOweExercise(), promotes=["*"])
