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
import os.path as pth

from openmdao.core.problem import Problem

from fastoad.io.xml import OpenMdaoXmlIO
from fastoad.io.xml.openmdao_legacy_io import OpenMdaoLegacy1XmlIO
from fastoad.modules.aerodynamics.components.cd0 import CD0
from fastoad.modules.aerodynamics.components.high_lift_aero import ComputeDeltaHighLift
from fastoad.openmdao.connections_utils import get_unconnected_inputs
from fastoad.modules.aerodynamics.components.oswald import OswaldCoefficient
from tests import root_folder

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), 'data')
CERAS_FILE_PATH = pth.join(root_folder, 'tests', 'io', 'xml', 'data', 'CeRAS01_baseline.xml')
AERO_INPUT_FILE_PATH = pth.join(DATA_FOLDER_PATH, 'aerodynamics_inputs.xml')


def create_inputs():
    """
    Completes 'aerodynamics_inputs.xml' with needed data for required componenets.
    Data are retrieved from 'CeRAS01_baseline.xml'
    """
    components = [ComputeDeltaHighLift(),
                  ComputeDeltaHighLift(landing_flag=True),
                  OswaldCoefficient(),
                  CD0()]

    ceras_reader = OpenMdaoLegacy1XmlIO(CERAS_FILE_PATH)
    aero_io = OpenMdaoXmlIO(AERO_INPUT_FILE_PATH)
    aero_io.path_separator = ':'

    # Variables that are part of the process but not expected in XML file
    ignore_list = ['xfoil:mach', 'reynolds_high_speed', 'cl_high_speed']

    for component in components:
        ivc_aero = aero_io.read()
        problem = Problem()
        problem.model.add_subsystem('inputs', ivc_aero, promotes=['*'])
        problem.model.add_subsystem('component', component, promotes=['*'])
        problem.setup(mode='fwd')
        mandatory, optional = get_unconnected_inputs(problem)
        vars = mandatory + optional
        var_names = [var.split('.')[-1] for var in vars]
        ivc_ceras = ceras_reader.read(only=var_names, ignore=ignore_list)

        for var_name in var_names:
            for (name, value, attributes) in ivc_ceras._indep_external:
                if name == var_name:
                    ivc_aero.add_output(var_name, val=value, units=attributes['units'])
                    break
        aero_io.write(ivc_aero)


if __name__ == '__main__':
    create_inputs()
