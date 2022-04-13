#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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

from dataclasses import asdict, dataclass


@dataclass
class BaseDataClass:
    """
    This class is a workaround for the following dataclass problem:

        If a dataclass defines a field with a default value, inheritor classes will not
        be allowed to define fields without default value, because then the non-default fields
        will follow a default field, which is forbidden.

    The chosen solution (from https://stackoverflow.com/a/53085935/16488238) is to always define
    default values, but mandatory fields will have the :attr:`_no_default` object as default.

    After initialization, the __post_init__ method will process fields and raise an error if
    a field has _no_default as value.
    """

    no_default = object()

    def __post_init__(self):
        for name, value in asdict(self).items():
            if value is self.__class__.no_default:
                raise TypeError(f"__init__ missing 1 required argument: '{name}'")
