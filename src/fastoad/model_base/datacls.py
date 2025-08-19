"""Dataclass utilities."""

from dataclasses import dataclass, fields

#: To be put as default value for dataclass fields that should not have a default value.
#: See :class:`BaseDataClass` for further information.
MANDATORY_FIELD = object()


@dataclass
class BaseDataClass:
    """
    This class is a workaround for the following dataclass problem:

        If a dataclass defines a field with a default value, inheritor classes will not
        be allowed to define fields without default value, because then the non-default fields
        will follow a default field, which is forbidden.

    The chosen solution (from https://stackoverflow.com/a/53085935/16488238) is to always define
    default values, but mandatory fields will have the :const:`MANDATORY_FIELD` object as default.

    After initialization, :meth:`__post_init__` will process fields and raise an error if
    a field has :const:`MANDATORY_FIELD` as value.
    """

    def __post_init__(self):
        field_dict = {field.name: getattr(self, field.name) for field in fields(self)}
        for name, value in field_dict.items():
            if value is MANDATORY_FIELD:
                raise TypeError(f"__init__ missing 1 required argument: '{name}'")
