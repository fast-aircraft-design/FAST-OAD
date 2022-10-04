from IPython.display import display

import ipywidgets as widgets


class ChoiceForOWE:
    def __init__(self):

        box_layout = widgets.Layout(
            display="flex", flex_flow="column", align_items="stretch", width="100%"
        )

        self.choice_button = widgets.ToggleButtons(
            options=["Corrected component", "Exercise component"],
            disabled=False,
            button_style="info",
            tooltips=[
                "Toggle this button to use the correct component",
                "Toggle this button to use the component left as exercise",
            ],
            icon=["fa-check-square-o", "fa-wrench"],
            style={"button_width": "48%"},
            layout=box_layout,
        )
        self.choice = "correct"

        self.choice_button.observe(self.select_component)

        display(self.choice_button)

    def select_component(self, b):

        if self.choice_button.value == "Corrected component":
            self.choice = "correct"
        else:
            self.choice = "exercise"
