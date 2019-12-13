"""
API
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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

from fastoad.io.configuration import ConfiguredProblem
from fastoad.io.xml import OMXmlIO, OMLegacy1XmlIO


# TODO: Must this class fusioned with ConfiguredProblem?
class FastProblem(ConfiguredProblem):

    def __init__(self, conf_file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(conf_file)

    def gen_inputs(self):
        self.write_needed_inputs()

    def gen_inputs_from(self, input_file=None):
        self.write_needed_inputs(OMXmlIO(input_file))

    def gen_inputs_from_legacy(self, input_file=None):
        self.write_needed_inputs(OMLegacy1XmlIO(input_file))

    def run_eval(self):
        self.read_inputs()
        self.run_model()
        self.write_outputs()

    def run_optim(self):
        self.read_inputs()
        self.run_driver()
        self.write_outputs()
