from IPython.display import display

import ipywidgets as widgets


class ChoiceForOWE:
    def __init__(self):

        self.button_correct_component = widgets.Button(
            description="Corrected component",
            disabled=False,
            button_style="info",
            tooltips=[
                "Toggle this button to use the correct component",
            ],
            icon="fa-check-square-o",
            layout=widgets.Layout(width="50%", height="50px"),
        )
        self.button_exercise_component = widgets.Button(
            description="Exercise component",
            disabled=False,
            button_style="info",
            tooltips=[
                "Toggle this button to use the component left as exercise",
            ],
            icon="fa-wrench",
            layout=widgets.Layout(width="50%", height="50px"),
        )
        self.choice = "correct"

        self.button_correct_component.on_click(self.select_correct_component)
        self.button_exercise_component.on_click(self.select_exercise_component)

        self.buttons = widgets.HBox([self.button_correct_component, self.button_exercise_component])

        display(self.buttons)

    def select_correct_component(self, b):

        self.choice = "correct"

    def select_exercise_component(self, b):

        self.choice = "exercise"
