from typing import Any

import panel as pn
from panel import param
from panel.viewable import Viewable
from param import ClassSelector

# Initialize the Panel extension
pn.extension()


class Header(pn.viewable.Viewer):
    conf_file_path = param.FileInput(accept=".yml, .yaml")

    def __panel__(self) -> Viewable:
        return pn.Row(
            pn.layout.Spacer(width=200),
            "Configuration File",
            self.conf_file_path,
        )


class ModelDefinition(pn.viewable.Viewer):
    models = param.Column()

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
    input_file_path = param.FileInput(accept=".xml")
    output_file_path = param.FileInput(accept=".xml")
    model_definition = ClassSelector(class_=ModelDefinition)

    def __init__(self, **params):
        super().__init__(**params)
        self.model_definition = ModelDefinition()

    def __panel__(self) -> Viewable:
        input_file_widget = pn.Row(
            "Input Data file", self.input_file_path, sizing_mode="stretch_width"
        )
        output_file_widget = pn.Row(
            "Output Data file", self.input_file_path, sizing_mode="stretch_width"
        )
        return pn.Column(
            input_file_widget,
            output_file_widget,
            pn.layout.Divider(),
            self.model_definition,
            pn.layout.Divider(),
            sizing_mode="stretch_width",
        )


class MainArea(pn.viewable.Viewer):
    def __panel__(self) -> Viewable:
        pass


class BaseTab(pn.Column):
    data_tab = param.Column(name="Data")
    visu_tab = param.Column(name="Visualisation")
    tabs = param.Tabs(data_tab, visu_tab)


class MainTab(BaseTab):
    def __init__(self, *objects: Any, **params: Any):
        super().__init__(*objects, **params)

        tab_name_input = pn.widgets.TextInput(name="Tab Name")
        add_tab_button = pn.widgets.Button(name="Add Tab", button_type="success")
        add_tab_button.on_click(self.add_tab)

        self.data_tab.append()

    def add_tab(self, event):
        tab_name = tab_name_input.value
        if tab_name:
            new_tab = pn.Column(f"Content of {tab_name}")
            tabs.append((tab_name, new_tab))
            tab_name_input.value = ""  # Clear the input field


# # Create header with "Run" button
# run_button = pn.widgets.Button(name="Run", button_type="primary")
# header = pn.Row(run_button)
#
# # Create main area with tabs
# tab_name_input = pn.widgets.TextInput(name="Tab Name")
# add_tab_button = pn.widgets.Button(name="Add Tab", button_type="success")
# add_tab_button.on_click(add_tab)
# initial_tab = pn.Column(tab_name_input, add_tab_button)
# tabs = pn.Tabs(("Tab 1", initial_tab), sizing_mode="stretch_both")
#
# # Create sidebar for navigation
# sidebar = pn.Column(pn.pane.Markdown("## Sidebar\n- [Tab 1](#)"))

# Assemble the layout
layout = pn.template.MaterialTemplate(
    title="Panel Web App",
    header=Header(),
    sidebar=SideBar(),
    main=MainArea(),
)

# Serve the app
layout.servable()
