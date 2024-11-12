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
from panel.widgets import FileInput, CodeEditor


class CodeEditorApp(pn.viewable.Viewer):
    file_path = param.String(default=None, doc="Path to the file to be loaded")
    code = param.String(default="", doc="Code content from the file")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_input = FileInput(accept=".py", callback=self.load_file)
        self.code_editor = CodeEditor(value=self.code, language="python")

    def load_file(self, event):
        if event.new:
            with open(event.filename, "r") as file:
                self.code = file.read()
                self.code_editor.value = self.code

    def __panel__(self):
        return pn.Column(self.file_input, self.code_editor)


# Example usage
app = CodeEditorApp()
app.servable()
