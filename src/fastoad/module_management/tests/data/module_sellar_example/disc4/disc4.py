"""Sample discipline 4"""

import openmdao.ap as om

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("module_management_test.sellar.disc4", domain=ModelDomain.GEOMETRY)
class RegisteredDisc4(om.ExplicitComponent):
    """Disc 4 which can be registered but can be used"""

    def setup(self):
        pass

    # pylint: disable=invalid-name
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        pass
