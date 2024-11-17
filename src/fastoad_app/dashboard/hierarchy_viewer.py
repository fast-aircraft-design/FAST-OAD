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

import panel as pn
import param
from panel.custom import PyComponent
from panel.viewable import Viewable


class HierarchyViewer(pn.viewable.Viewer):
    debug = pn.param.StaticText()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = Group(name="Root Model")
        self.problem = Group(name="Problem", components=[self.model])

        pn.bind(self.update, self.problem.title, watch=True)

    def update(self, event):
        self.debug.value = str(event)

    def __panel__(self) -> Viewable:
        return pn.Column(self.debug, self.problem)


class Group(pn.viewable.Viewer):
    name = param.String("group")
    components = param.List()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = Header(name="group")

    def __panel__(self) -> Viewable:
        return pn.layout.Card(*self.components, name=self.name, header=self.title)


class Header(PyComponent):
    name = param.String("group")

    def __panel__(self) -> Viewable:
        return pn.widgets.Toggle(name=self.name)


class Model(pn.viewable.Viewer):
    name = param.String()
    id = param.String()

    def __panel__(self) -> Viewable:
        return pn.layout.Card(pn.widgets.TextInput(name="id", value=self.id), title=self.name)
