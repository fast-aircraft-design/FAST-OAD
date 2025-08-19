

from fastoad.module_management.service_registry import RegisterSpecializedService


class DummyBase:
    def my_class(self):
        return self.__class__.__name__


class RegisterDummyService(RegisterSpecializedService, base_class=DummyBase):
    pass
