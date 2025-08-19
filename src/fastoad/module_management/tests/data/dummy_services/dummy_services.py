from fastoad.module_management.tests.test_register_specialized_service import (
    DummyBase,
    RegisterDummyServiceA,
)


@RegisterDummyServiceA("dummy.provider.1")
class Dummy1(DummyBase):
    pass


@RegisterDummyServiceA("dummy.provider.2")
class Dummy2(DummyBase):
    pass
