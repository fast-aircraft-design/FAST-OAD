"""Sellar discipline 1"""

from fastoad._utils.sellar.disc1 import BasicDisc1
from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem(
    "module_management_test.sellar.disc1", desc="some text", domain=ModelDomain.OTHER
)
class RegisteredDisc1(BasicDisc1):
    pass
