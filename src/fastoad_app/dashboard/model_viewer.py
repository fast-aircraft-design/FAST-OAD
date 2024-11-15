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
from panel.viewable import Viewable


class Group(pn.viewable.Viewer):
    name = param.String()
    components = param.List()

    def __panel__(self) -> Viewable:
        return pn.layout.Card(*self.components, title=self.name)


class Model(pn.viewable.Viewer):
    name = param.String()
    id = param.String()

    def __panel__(self) -> Viewable:
        return pn.layout.Card(pn.widgets.TextInput(name="id", value=self.id), title=self.name)
