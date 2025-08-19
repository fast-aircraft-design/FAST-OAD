"""Sellar discipline 3"""

import openmdao.api as om

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.exceptions import FastBundleLoaderUnavailableFactoryError
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("module_management_test.sellar.disc3", domain=ModelDomain.GEOMETRY)
class RegisteredDisc3(om.ExplicitComponent):
    """Disc 3 which can be registered but can't be used except certain conditions"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        raise FastBundleLoaderUnavailableFactoryError(
            "This module is only available on days that don't end in 'day' and on the 30th of "
            "February"
        )

    def setup(self):
        pass

    # pylint: disable=invalid-name
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        pass
