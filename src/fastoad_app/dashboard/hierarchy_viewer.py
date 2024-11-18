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
from dataclasses import dataclass

import panel as pn
import param
from panel.viewable import Viewable

from fastoad_app.dashboard.observer_base import IObserver, Observed


@dataclass
class ButtonHub(Observed):
    active_element: IObserver = None

    def signal(self, element: IObserver):
        self.active_element = element
        self.notify()

    def notify(self) -> None:
        for observer in self._observers:
            if observer is not self.active_element:
                observer.update(self)


BUTTON_HUB = ButtonHub()


class HierarchyViewer(pn.viewable.Viewer):
    debug = pn.param.StaticText()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.problem = Group(name="Problem")
        BUTTON_HUB.attach(self.problem)

        self.model = Group(name="Root Model")
        self.problem.add_element(self.model)

        pn.bind(self.update, self.problem.button, watch=True)

    def update(self, event):
        self.debug.value = str(event)

    def __panel__(self) -> Viewable:
        return pn.Column(self.debug, self.problem)


class Element(pn.viewable.Viewer, IObserver):
    name = param.String()
    components = param.List()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.button = pn.widgets.Button(name=self.name, on_click=self.update)
        self.card = pn.layout.Card(name=self.name, header=pn.layout.Row(self.button))

    def __panel__(self) -> Viewable:
        self.card[:] = [*self.components]
        return self.card

    def update(self, event=None):
        if event is BUTTON_HUB:
            self.button.button_type = "default"
        else:
            BUTTON_HUB.signal(self)
            self.button.button_type = "primary"


class Group(Element):
    def add_element(self, element: Element):
        self.components.append(element)
        BUTTON_HUB.attach(element)


class Model(Element):
    id = param.String()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.components[:] = [pn.widgets.TextInput(name="id", value=self.id)]
