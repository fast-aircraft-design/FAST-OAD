#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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
import openmdao.api as om
import panel as pn
from openmdao.core.constants import _UNDEFINED
from panel.viewable import Viewer
from param import ClassSelector, Undefined


class OptionsParameter(ClassSelector):
    def __init__(self, default=Undefined, **params):
        super().__init__(default=default, class_=om.OptionsDictionary, **params)


class OptionsViewer(Viewer):
    value = OptionsParameter(default=om.OptionsDictionary())

    def __panel__(self):
        return pn.Column(
            *[
                self._get_option_view(name, definition)
                for name, definition in self.value._dict.items()
            ]
        )

    def _get_option_view(self, name, option_definition):
        # if self.definition.types is None:
        if option_definition["val"] is _UNDEFINED:
            value = None
        else:
            value = option_definition["val"]

        widget = pn.widgets.TextInput(name=name, value=value)

        return widget


if __name__ == "__main__":
    ov = OptionsViewer()
    ov.value = om.OptionsDictionary()
    ov.value.declare("toto", types=str)
    ov.value.declare("tutu", types=int)
    print(ov.value._dict)
    pn.serve(ov)
