# This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
# Copyright (c) 2025 ONERA & ISAE-SUPAERO
# FAST-OAD is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later

import ipywidgets as widgets
from IPython.display import display


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
