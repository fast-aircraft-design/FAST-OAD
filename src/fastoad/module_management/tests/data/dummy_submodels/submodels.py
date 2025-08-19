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
