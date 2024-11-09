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
from panel.viewable import Viewable

from .base import BaseTab


class Header(pn.viewable.Viewer):
    # conf_file_path = pn.param.FileInput(accept=".yml, .yaml")

    def __init__(self, **params):
        super().__init__(**params)
        self.conf_file_path = pn.widgets.FileInput(accept=".yml, .yaml")

    def __panel__(self) -> Viewable:
        return pn.Row(
            pn.layout.Spacer(width=200),
            "Configuration File",
            self.conf_file_path,
        )


class ModelDefinition(pn.viewable.Viewer):
    models = pn.param.Column()

    def _add_model(self, event):
        self.models.append(pn.layout.Card())

    def __panel__(self):
        return pn.WidgetBox(
            "# Model",
            pn.widgets.Button(name="Add Model", on_click=self._add_model),
            self.models,
            name="Model",
            sizing_mode="stretch_width",
        )


class SideBar(pn.viewable.Viewer):
    eval_button = pn.param.Button(name="Evaluate")
    optim_button = pn.param.Button(name="Optimize")

    def __init__(self, **params):
        super().__init__(**params)
        self.model_definition = ModelDefinition()

    def __panel__(self) -> Viewable:
        return pn.Column(
            self.eval_button,
            pn.layout.Divider(),
            self.optim_button,
            sizing_mode="stretch_width",
        )


class MainArea(pn.viewable.Viewer):
    tabs = pn.param.Tabs()

    def __panel__(self) -> Viewable:
        return self.tabs


class FastoadApp:
    def __init__(self):
        super().__init__()
        self.header = Header()
        self.sidebar = SideBar()
        self.main_area = MainArea()

        self.layout = pn.template.MaterialTemplate(
            title="Panel Web App",
            header=self.header,
            sidebar=self.sidebar,
            main=self.main_area,
        )

        self.header.conf_file_path.param.watch(self.load_configuration, "value")

        # pn.bind(self.load_configuration, self.header.conf_file_path, watch=True)

        self.layout.servable()

    def load_configuration(self, file_path):
        self.main_area.tabs.clear()
        if file_path:
            self.main_area.tabs.append(("Problem", BaseTab()))
        else:
            self.main_area.tabs.append(("Not a Problem", BaseTab()))
