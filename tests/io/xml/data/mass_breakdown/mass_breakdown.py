"""
Main components for mass breakdown
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
from typing import List

import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent
from openmdao.solvers.linear.linear_block_gs import LinearBlockGS
from openmdao.solvers.nonlinear.nonlinear_block_gs import NonlinearBlockGS
from openmdao.vectors.vector import Vector

from fastoad.modules.mass_breakdown.a_airframe import WingWeight, FuselageWeight, EmpennageWeight, \
    FlightControlsWeight, LandingGearWeight, PylonsWeight, PaintWeight
from fastoad.modules.mass_breakdown.b_propulsion import EngineWeight, FuelLinesWeight, \
    UnconsumablesWeight
from fastoad.modules.mass_breakdown.c_systems import PowerSystemsWeight, LifeSupportSystemsWeight, \
    NavigationSystemsWeight, TransmissionSystemsWeight, FixedOperationalSystemsWeight, \
    FlightKitWeight
from fastoad.modules.mass_breakdown.cs25 import Loads
from fastoad.modules.mass_breakdown.d_furniture import CargoConfigurationWeight, \
    PassengerSeatsWeight, FoodWaterWeight, SecurityKitWeight, ToiletsWeight
from fastoad.modules.mass_breakdown.e_crew import CrewWeight
from fastoad.modules.mass_breakdown.options import OpenMdaoOptionDispatcherGroup, \
    ENGINE_LOCATION_OPTION, TAIL_TYPE_OPTION, AIRCRAFT_TYPE_OPTION
from fastoad.modules.mass_breakdown.update_mlw_and_mzfw import UpdateMLWandMZFW


class MassBreakdown(OpenMdaoOptionDispatcherGroup):
    """
    The top group for solving mass breakdown
    """

    def initialize(self):
        # TODO: Manage options through constants or enums
        self.options.declare(ENGINE_LOCATION_OPTION, types=float, default=1.0)
        self.options.declare(TAIL_TYPE_OPTION, types=float, default=0.)
        self.options.declare(AIRCRAFT_TYPE_OPTION, types=float, default=2.0)

    def setup(self):
        self.add_subsystem('oew', OperatingEmptyWeight(), promotes=['*'])
        self.add_subsystem('update_mzfw_and_mlw', UpdateMLWandMZFW(), promotes=['*'])

    def configure(self):
        super(MassBreakdown, self).configure()

        # Solvers setup
        self.nonlinear_solver = NonlinearBlockGS()
        self.nonlinear_solver.options['iprint'] = 0
        self.nonlinear_solver.options['maxiter'] = 50
        self.linear_solver = LinearBlockGS()
        self.linear_solver.options['iprint'] = 0


class OperatingEmptyWeight(OpenMdaoOptionDispatcherGroup):
    """ Operating Empty Weight (OEW) estimation

    This group aggregates weight from all components of the aircraft.
    """

    def initialize(self):
        # TODO: Manage options through constants or enums
        self.options.declare(ENGINE_LOCATION_OPTION, types=float, default=1.0)
        self.options.declare(TAIL_TYPE_OPTION, types=float, default=0.)
        self.options.declare(AIRCRAFT_TYPE_OPTION, types=float, default=2.0)

    def setup(self):
        # Airframe
        self.add_subsystem('loads', Loads(), promotes=['*'])
        self.add_subsystem('wing_weight', WingWeight(), promotes=['*'])
        self.add_subsystem('fuselage_weight', FuselageWeight(), promotes=['*'])
        self.add_subsystem('empennage_weight', EmpennageWeight(), promotes=['*'])
        self.add_subsystem('flight_controls_weight', FlightControlsWeight(), promotes=['*'])
        self.add_subsystem('landing_gear_weight', LandingGearWeight(), promotes=['*'])
        # Engine have to be computed before pylons
        self.add_subsystem('engines_weight', EngineWeight(), promotes=['*'])
        self.add_subsystem('pylons_weight', PylonsWeight(), promotes=['*'])
        self.add_subsystem('paint_weight', PaintWeight(), promotes=['*'])
        # Propulsion
        self.add_subsystem('fuel_lines_weight', FuelLinesWeight(), promotes=['*'])
        self.add_subsystem('unconsumables_weight', UnconsumablesWeight(), promotes=['*'])
        # Systems
        self.add_subsystem('power_systems_weight', PowerSystemsWeight(), promotes=['*'])
        self.add_subsystem('life_support_systems_weight', LifeSupportSystemsWeight(),
                           promotes=['*'])
        self.add_subsystem('navigation_systems_weight', NavigationSystemsWeight(), promotes=['*'])
        self.add_subsystem('transmission_systems_weight', TransmissionSystemsWeight(),
                           promotes=['*'])
        self.add_subsystem('fixed_operational_systems_weight', FixedOperationalSystemsWeight(),
                           promotes=['*'])
        self.add_subsystem('flight_kit_weight', FlightKitWeight(), promotes=['*'])
        # Cargo and furniture
        self.add_subsystem('cargo_configuration_weight', CargoConfigurationWeight(), promotes=['*'])
        self.add_subsystem('passenger_seats_weight', PassengerSeatsWeight(), promotes=['*'])
        self.add_subsystem('food_water_weight', FoodWaterWeight(), promotes=['*'])
        self.add_subsystem('security_kit_weight', SecurityKitWeight(), promotes=['*'])
        self.add_subsystem('toilets_weight', ToiletsWeight(), promotes=['*'])
        # Crew
        self.add_subsystem('crew_weight', CrewWeight(), promotes=['*'])
        self.add_subsystem('link_variables', LinkWeightVariables(), promotes=['*'])


class LinkWeightVariables(ExplicitComponent):
    """ Computes overall weight from all weight computations

    Gets outputs from all subsystems to output global weight:
        - for each category (airframe, propulsion, systems, furniture, crew)
        - for the entire aircraft, i.e. OEW
    """

    def initialize(self):
        # TODO: decide if options are the correct way to handle these lists
        airframe_names = ['A1', 'A2', 'A31', 'A32', 'A4', 'A51', 'A52', 'A6', 'A7']
        propulsion_names = ['B1', 'B2', 'B3']
        systems_names = ['C11', 'C12', 'C13', 'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27',
                         'C3', 'C4', 'C51', 'C52', 'C6']
        furniture_names = ['D1', 'D2', 'D3', 'D4', 'D5']

        self.options.declare('airframe_names', default=airframe_names, types=list)
        self.options.declare('propulsion_names', default=propulsion_names, types=list)
        self.options.declare('systems_names', default=systems_names, types=list)
        self.options.declare('furniture_names', default=furniture_names, types=list)

    def setup(self):
        airframe_names = self.options['airframe_names']
        propulsion_names = self.options['propulsion_names']
        systems_names = self.options['systems_names']
        furniture_names = self.options['furniture_names']

        self.__add_weight_inputs('weight_airframe', airframe_names)
        self.__add_weight_inputs('weight_propulsion', propulsion_names)
        self.__add_weight_inputs('weight_systems', systems_names)
        self.__add_weight_inputs('weight_furniture', furniture_names)
        self.add_input('weight_crew:E', val=np.nan, units='kg')

        self.add_output('weight_airframe:A', units='kg')
        self.add_output('weight_propulsion:B', units='kg')
        self.add_output('weight_systems:C', units='kg')
        self.add_output('weight_furniture:D', units='kg')
        self.add_output('weight:OEW', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        weight_a = self.__compute_category_weight(inputs, 'weight_airframe',
                                                  self.options['airframe_names'])
        weight_b = self.__compute_category_weight(inputs, 'weight_propulsion',
                                                  self.options['propulsion_names'])
        weight_c = self.__compute_category_weight(inputs, 'weight_systems',
                                                  self.options['systems_names'])
        weight_d = self.__compute_category_weight(inputs, 'weight_furniture',
                                                  self.options['furniture_names'])
        weight_e = inputs['weight_crew:E']

        oew = weight_a + weight_b + weight_c + weight_d + weight_e

        outputs['weight_airframe:A'] = weight_a
        outputs['weight_propulsion:B'] = weight_b
        outputs['weight_systems:C'] = weight_c
        outputs['weight_furniture:D'] = weight_d
        outputs['weight:OEW'] = oew

    def __add_weight_inputs(self, category_name: str,
                            subpart_names: List[str]):
        """
        Populates self.inputs with weight variables

        Variable names are built from category_name and each element of
        subpart_names

        :param category_name:
        :param subpart_names:
        """
        for name in self.__get_subpart_weight_variables(category_name, subpart_names):
            self.add_input(name, val=np.nan, units='kg')

    @classmethod
    def __compute_category_weight(cls, inputs: Vector, category_name: str,
                                  subpart_names: List[str]):
        """
        Sums the weights of all sub-parts of the category

        It assumes that weight of each subpart is in inputs with a
        variable name like 'my_category:my_subpart_name'

        :type inputs:
        :param category_name:
        :param subpart_names:

        :return: sum of weights after iterating through subpart_names
        """
        input_ids = cls.__get_subpart_weight_variables(category_name, subpart_names)
        return sum([inputs[input_id] for input_id in input_ids])

    @staticmethod
    def __get_subpart_weight_variables(category_name: str, subpart_names: List[str]):
        """

        :param category_name:
        :param subpart_names:
        :return: weight variable names by assembling category_name with each
        element of subpart_names
        """
        return ['%s:%s' % (category_name, name) for name in subpart_names]
