"""Sellar discipline 3"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2025 ONERA & ISAE-SUPAERO
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

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

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        pass
