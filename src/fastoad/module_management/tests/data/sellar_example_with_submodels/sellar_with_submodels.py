"""Sellar discipline 1"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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


from fastoad._utils.sellar.sellar_base import ISellarFactory
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem, RegisterSubmodel
from fastoad.openmdao.tests.openmdao_sellar_example.sellar import SellarModel


class SubModelBasedSellarFactory(ISellarFactory):
    def create_disc1(self):
        return RegisterSubmodel.get_submodel("required_submodel.sellar.disc1")

    def create_disc2(self):
        return RegisterSubmodel.get_submodel("required_submodel.sellar.disc2")

    def create_objective_function(self):
        return RegisterSubmodel.get_submodel("required_submodel.sellar.objective")

    def create_constraints(self):
        return RegisterSubmodel.get_submodel("required_submodel.sellar.constraints")


@RegisterOpenMDAOSystem("test_assembly.sellar.standard")
class SubModelBasedSellar(SellarModel):
    def initialize(self):
        super().initialize()
        self.options["sellar_factory"] = SubModelBasedSellarFactory()


@RegisterOpenMDAOSystem(
    "test_assembly.sellar.alternate_1",
    activated_submodels={
        "required_submodel.sellar.disc1": "submodel.sellar.disc1.alternate",
        "required_submodel.sellar.objective": "submodel.sellar.objective",
    },
)
class AlternateSubModelBasedSellar1(SubModelBasedSellar):
    pass


@RegisterOpenMDAOSystem(
    "test_assembly.sellar.alternate_2",
    activated_submodels={
        "required_submodel.sellar.disc1": "submodel.sellar.disc1.alternate",
        "required_submodel.sellar.objective": "submodel.sellar.objective",
    },
)
class AlternateSubModelBasedSellar2(SubModelBasedSellar):
    pass


@RegisterOpenMDAOSystem(
    "test_assembly.sellar.alternate_3",
    activated_submodels={
        "required_submodel.sellar.disc1": "submodel.sellar.disc1.alternate",
        "required_submodel.sellar.objective": "submodel.sellar.objective.alternate",
    },
)
class AlternateSubModelBasedSellar3(SubModelBasedSellar):
    pass
