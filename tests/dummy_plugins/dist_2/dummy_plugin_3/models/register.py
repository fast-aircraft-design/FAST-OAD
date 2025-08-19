

from .declared_dummy_components import DeclaredDummy1, DeclaredDummy2
from ....base import RegisterDummyService

RegisterDummyService("test.plugin.declared.1")(DeclaredDummy1)
RegisterDummyService("test.plugin.declared.2")(DeclaredDummy2)
