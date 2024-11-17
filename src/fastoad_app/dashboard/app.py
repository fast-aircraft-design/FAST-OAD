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
from pathlib import Path

import panel as pn
import param
from panel.viewable import Viewable

from fastoad.io.configuration import FASTOADProblemConfigurator
from fastoad_app.dashboard.hierarchy_viewer import HierarchyViewer, Model


class Header(pn.viewable.Viewer):
    # conf_file_path = pn.param.FileInput(accept=".yml, .yaml")

    def __init__(self, **params):
        super().__init__(**params)
        # self.conf_file_path = pn.widgets.FileInput(
        #     accept=".yml, .yaml",
        # )

    def __panel__(self) -> Viewable:
        return pn.Row(
            pn.layout.Spacer(width=200),
            "Configuration File",
            # self.conf_file_path,
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
    conf_file_path_input = pn.param.TextInput(sizing_mode="stretch_width")

    def __init__(self, **params):
        super().__init__(**params)
        self.configuration = FASTOADProblemConfigurator()
        self.problem_definition = HierarchyViewer()
        self.problem_definition.model.components.extend(
            [
                Model(name="geometry", id="toto.geom"),
                Model(name="aerodynamics", id="toto.aero"),
            ]
        )
        self.file_loader = pn.widgets.FileSelector(file_pattern="*.y*ml", only_files=True)
        self.file_dialog = pn.Column(height=0, width=0)
        self.conf_file_path_input.value = pn.bind(
            self.choose_configuration_file, file_paths=self.file_loader
        )

        pn.bind(self.load_configuration, file_path=self.conf_file_path_input, watch=True)

    def choose_configuration_file(self, file_paths):
        if len(file_paths) == 0:
            return ""
        if len(file_paths) > 1:
            self.file_loader.value[:] = [file_paths[-1]]

        return file_paths[-1]

    def load_configuration(self, file_path):
        if Path(file_path).is_absolute() and Path(file_path).is_file():
            self.configuration.load(file_path)

    def pick_file(self, event):
        self.file_dialog[:] = [
            pn.layout.FloatPanel(
                self.file_loader,
                name="Choose configuration file",
                contained=False,
                position="center",
            )
        ]

    def __panel__(self) -> Viewable:
        configuration_loader = pn.layout.WidgetBox(
            "Configuration file",
            pn.layout.Row(
                pn.widgets.Button(name="Choose", on_click=self.pick_file),
                self.conf_file_path_input,
            ),
            sizing_mode="stretch_width",
        )
        return pn.layout.Column(
            configuration_loader,
            pn.layout.Divider(),
            self.eval_button,
            self.optim_button,
            pn.layout.Divider(),
            self.problem_definition,
            self.file_dialog,
            sizing_mode="stretch_width",
        )


class MainArea(pn.viewable.Viewer):
    file_input = pn.param.FileInput(accept=".yml,.yaml")
    editor = param.String("toto")

    def __init__(self, **kwargs):
        super().__init__()
        # pn.bind(self.update, self.file_input)
        self.file_input.param.watch(self.update, "value")

    def __panel__(self):
        """Map the string to appear as an Ace editor."""
        return pn.Column(
            self.file_input,
            pn.Param(
                self.param,
                widgets=dict(
                    editor=dict(
                        type=pn.widgets.CodeEditor, language="yaml", sizing_mode="stretch_both"
                    )
                ),
            ),
        )

    def update(self, event):
        self.editor = self.file_input.value.decode("utf-8")


#
# class MainArea(pn.viewable.Viewer):
#     tabs = pn.param.Tabs()
#     editor = param.ClassSelector(
#         class_=pn.widgets.CodeEditor,
#         default=pn.widgets.CodeEditor(
#             sizing_mode="stretch_width", language="yaml", value="load conf here"
#         ),
#         instantiate=True,
#     )
#
#     def __panel__(self) -> Viewable:
#         return pn.Column("Main Area", self.editor, self.tabs)
#
#     def load_configuration_file(self, file_path):
#         yaml = YAML(typ="safe")
#         with open(file_path) as yaml_file:
#             self.editor.value = yaml.load(yaml_file)


class FastoadApp:
    def __init__(self):
        self.header = Header()
        self.sidebar = SideBar()
        self.main_area = MainArea()

        self.layout = pn.template.MaterialTemplate(
            title="Panel Web App",
            header=self.header,
            sidebar=self.sidebar,
            main=self.main_area,
        )

        # self.header.conf_file_path.param.watch(self.load_configuration_file, "value")

        # pn.bind(self.load_configuration_file, self.header.conf_file_path, watch=True)

        self.layout.servable()

    # def load_configuration_file(self, file_path):
    #     self.main_area.tabs.append(pn.Column(str(file_path.new)))
    #     self.main_area.editor.value = file_path.new
