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


class OptionWidgetFactory:
    @classmethod
    def get_option_viewer(cls, name, option_definition):
        print(option_definition["deprecation"])
        if option_definition["deprecation"] and option_definition["deprecation"][1]:
            return None

        widget_class, widget_kwargs = cls._get_common_kwargs(name, option_definition)

        if option_definition["deprecation"]:
            widget_kwargs["background"] = "gray"
            widget_kwargs["description"] = option_definition["deprecation"][0]

        if option_definition["values"] is not None:
            widget_class = pn.widgets.Select
            widget_kwargs["options"] = option_definition["values"]

        elif option_definition["lower"] is not None and option_definition["upper"] is not None:
            del widget_kwargs["description"]
            widget_kwargs["fixed_start"] = option_definition["lower"]
            widget_kwargs["fixed_end"] = option_definition["upper"]

            try:
                types = list(option_definition["types"])
            except TypeError:
                types = [option_definition["types"]]
            if any(map(lambda t: issubclass(t, float), types)):
                widget_class = pn.widgets.EditableFloatSlider
            else:
                widget_class = pn.widgets.EditableIntSlider

            if widget_kwargs["value"] is None:
                widget_kwargs["value"] = widget_kwargs["fixed_start"]

        widget = widget_class(**widget_kwargs)

        return widget

    @classmethod
    def _get_common_kwargs(cls, name, option_definition):
        widget_kwargs = {"name": name}
        widget_class = pn.widgets.TextInput
        if option_definition["val"] is _UNDEFINED:
            widget_kwargs["value"] = None
        elif option_definition["has_been_set"]:
            widget_kwargs["value"] = option_definition["val"]
        else:
            widget_kwargs["value"] = option_definition["val"]
        if option_definition["desc"]:
            widget_kwargs["description"] = option_definition["desc"]
        return widget_class, widget_kwargs


class OptionsViewer(Viewer):
    value = OptionsParameter(default=om.OptionsDictionary())

    def __panel__(self):
        widgets = [
            OptionWidgetFactory.get_option_viewer(name, definition)
            for name, definition in self.value._dict.items()
        ]

        return pn.Card(*[w for w in widgets if w], title="Component")


options = om.OptionsDictionary()
options.declare("toto", types=str, desc="test desc")
options.declare("foo", values=["a", 1, True], desc="test desc")
options.declare(
    "deprecated", types=int, lower=0, upper=100, deprecation="deprecated", desc="test desc"
)
options.declare("tutu", types=int, lower=0, upper=100, desc="test desc")
options.declare("truc", types=float, lower=-10.0, upper=100.0, desc="test desc")
print(options._dict)
options["deprecated"] = 50
ov = OptionsViewer(value=options).servable()
