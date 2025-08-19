# This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
# Copyright (c) 2025 ONERA & ISAE-SUPAERO
# FAST-OAD is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later

import openmdao.api as om

from fastoad.module_management.exceptions import FastBundleLoaderUnavailableFactoryError
from fastoad.module_management.service_registry import RegisterSubmodel


@RegisterSubmodel("requirement.1", "req.1.submodel")
class UniqueSubmodelForRequirement1(om.ExplicitComponent):
    pass


@RegisterSubmodel("requirement.2", "req.2.submodel.A")
class SubmodelAForRequirement2(om.ExplicitComponent):
    pass


@RegisterSubmodel("requirement.2", "req.2.submodel.B")
class SubmodelBForRequirement2(om.ExplicitComponent):
    pass


@RegisterSubmodel("requirement.2", "req.2.submodel.C")
class SubmodelCForRequirement2(om.ExplicitComponent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        raise FastBundleLoaderUnavailableFactoryError(
            "This submodel will only be available when pigs will fly"
        )
