"""
Demonstrates how to register components in OpenMDAOSystemFactory
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

from fastoad.module_management.openmdao_system_factory import OpenMDAOSystemFactory
from fastoad.modules.aerodynamics import Aerodynamics
from fastoad.modules.geometry import Geometry
from fastoad.modules.performances.breguet import Breguet
from fastoad.modules.propulsion.fuel_engine.rubber_engine import OMRubberEngine

OpenMDAOSystemFactory.register_system(Geometry, 'geometry'
                                      , {'Number': 1
                                          , 'Discipline': 'geometry'})
OpenMDAOSystemFactory.register_system(Aerodynamics, 'aerodynamics'
                                      , {'Number': 2
                                          , 'Discipline': 'aerodynamics'})
OpenMDAOSystemFactory.register_system(Breguet, 'performance'
                                      , {'Number': 3
                                          , 'Discipline': 'performance'})
OpenMDAOSystemFactory.register_system(OMRubberEngine, 'propulsion'
                                      , {'Number': 4
                                          , 'Discipline': 'propulsion'})
