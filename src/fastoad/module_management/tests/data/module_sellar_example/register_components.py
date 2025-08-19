"""
Demonstrates the alternate way register components in RegisterOpenMDAOSystem.
The main way would be to use the decorator directly on class definition.
"""

from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem

from .disc2.disc2 import RegisteredDisc2

RegisterOpenMDAOSystem("module_management_test.sellar.disc2", domain=ModelDomain.GEOMETRY)(
    RegisteredDisc2
)
