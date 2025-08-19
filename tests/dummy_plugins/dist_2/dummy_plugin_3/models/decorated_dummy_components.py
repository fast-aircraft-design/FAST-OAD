"""
Module in a subpackage where services are declared with decorators
"""


from ....base import DummyBase, RegisterDummyService


@RegisterDummyService("test.plugin.decorated.3")
class DecoratedDummy3(DummyBase):
    pass
