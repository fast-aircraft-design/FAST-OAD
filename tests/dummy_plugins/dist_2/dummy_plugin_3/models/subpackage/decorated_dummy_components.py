"""
Module where services are declared with decorators
"""


from .....base import DummyBase, RegisterDummyService


@RegisterDummyService("test.plugin.decorated.1")
class DecoratedDummy1(DummyBase):
    pass


@RegisterDummyService("test.plugin.decorated.2")
class DecoratedDummy2(DummyBase):
    pass
