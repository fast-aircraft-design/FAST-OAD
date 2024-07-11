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
    def get_widget_class(cls, option_definition):
        if option_definition["deprecation"] and option_definition["deprecation"][1]:
            return None

        if option_definition["types"]:
            try:
                option_types = list(option_definition["types"])
            except TypeError:
                option_types = [option_definition["types"]]
        else:
            option_types = []

        if option_definition["values"] is not None:
            widget_class = pn.widgets.Select
        elif option_definition["lower"] is not None and option_definition["upper"] is not None:
            if any(map(lambda t: issubclass(t, float), option_types)):
                widget_class = pn.widgets.EditableFloatSlider
            else:
                widget_class = pn.widgets.EditableIntSlider
        elif any(map(lambda t: issubclass(t, str), option_types)):
            widget_class = pn.widgets.TextInput
        else:
            widget_class = pn.widgets.LiteralInput

        return widget_class

    @classmethod
    def get_widget(cls, name, option_definition, widget_class):

        widget_kwargs = {"name": name}

        matching = {
            "value": "val",
            "desc": "description",
            "options": "values",
            "fixed_start": "lower",
            "fixed_end": "upper",
        }

        if option_definition["val"] is _UNDEFINED:
            if option_definition.get("default") is not None:
                widget_kwargs["value"] = option_definition["default"]
            elif issubclass(
                widget_class, (pn.widgets.EditableIntSlider, pn.widgets.EditableFloatSlider)
            ):
                widget_kwargs["value"] = widget_kwargs.get("fixed_start", 0)
            elif issubclass(widget_class, pn.widgets.Select):
                widget_kwargs["value"] = option_definition["values"][0]
            else:
                widget_kwargs["value"] = None
        elif option_definition["has_been_set"]:
            widget_kwargs["value"] = option_definition["val"]
        else:
            widget_kwargs["placeholder"] = option_definition["val"]

        for kwarg_name, option_key in matching.items():
            if option_definition.get(option_key) and hasattr(widget_class, kwarg_name):
                if option_definition[option_key] is not _UNDEFINED:
                    widget_kwargs[kwarg_name] = option_definition[option_key]

        return widget_class(**widget_kwargs)

    @classmethod
    def get_option_viewer(cls, name, option_definition):
        if option_definition["deprecation"] and option_definition["deprecation"][1]:
            return None

        widget_class = cls.get_widget_class(option_definition)
        widget = cls.get_widget(name, option_definition, widget_class)

        return widget


class OptionsViewer(Viewer):
    value = OptionsParameter(default=om.OptionsDictionary())

    def __panel__(self):
        widgets = []
        bindings = {}

        for name, definition in self.value._dict.items():
            widget = OptionWidgetFactory.get_option_viewer(name, definition)
            bindings[name] = widget
            widgets.append(widget)

        pn.bind(self.update_options, **bindings, watch=True)
        # bound_display = pn.panel(pn.bind(self.update_display, **bindings))
        # bound_display.visible = True
        return pn.Card(*[w for w in widgets if w], title="Options")

    def update_options(self, **kwargs):
        print("update_options")
        for name, value in kwargs.items():
            self.value[name] = value

    def update_display(self, **kwargs):
        print("update_display")
        self.update_options(**kwargs)
        return {n: v for n, v in self.value.items()}


options = om.OptionsDictionary()
options.declare("toto", default="foo", types=str, desc="test desc")
options.declare("foo", values=["a", 10, True], desc="test desc")
options.declare(
    "deprecated", types=int, lower=0, upper=10, deprecation="deprecated", desc="test desc"
)
options.declare("tutu", types=int, lower=0, upper=10, desc="test desc")
# options.declare("truc", types=float, lower=0.0, upper=100.0, desc="test desc")
options.declare("titi", desc="test desc")
# print(options._dict)
# options["deprecated"] = 50
ov = OptionsViewer(value=options)
ov.servable()
display = pn.widgets.LiteralInput(name="options")


def print_options(toto):
    display.value = {name: value for name, value in ov.value.items()}


pn.widgets.Button(name="result", on_click=print_options).servable()
display.servable()
