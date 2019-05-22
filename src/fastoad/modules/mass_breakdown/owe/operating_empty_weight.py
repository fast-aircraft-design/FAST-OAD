"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""

#      This file is part of FAST : A framework for rapid Overall Aircraft Design
#      Copyright (C) 2019  ONERA/ISAE
#      FAST is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
from openmdao.api import Group

from fastoad.modules.mass_breakdown.cs25 import Loads
from fastoad.modules.mass_breakdown.functions_A import EmpennageWeight, FlightControlsWeight, \
    FuselageWeight, \
    LandingGearWeight, PaintWeight, PylonsWeight, WingWeight
from fastoad.modules.mass_breakdown.functions_B import EngineWeight, FuelLinesWeight, \
    UnconsumablesWeight
from fastoad.modules.mass_breakdown.functions_C import FixedOperationalSystemsWeight, \
    FlightKitWeight, \
    LifeSupportSystemsWeight, NavigationSystemsWeight, PowerSystemsWeight, TransmissionSystemsWeight
from fastoad.modules.mass_breakdown.functions_D import CargoConfigurationWeight, FoodWaterWeight, \
    PassengerSeatsWeight, \
    SecurityKitWeight, ToiletsWeight
from fastoad.modules.mass_breakdown.functions_E import CrewWeight
from .link_weight_variables import LinkWeightVariables


class OperatingEmptyWeight(Group):

    def initialize(self):
        self.options.declare('engine_location', types=float, default=1.0)
        self.options.declare('tail_type', types=float, default=0.)
        self.options.declare('ac_type', types=float, default=2.0)

    def setup(self):
        self.engine_location = self.options['engine_location']
        self.tail_type = self.options['tail_type']
        self.ac_type = self.options['ac_type']

        # Airframe
        self.add_subsystem('loads', Loads(), promotes=['*'])
        self.add_subsystem('wing_weight', WingWeight(), promotes=['*'])
        self.add_subsystem('fuselage_weight', FuselageWeight(), promotes=['*'])
        self.add_subsystem('empennage_weight', EmpennageWeight(engine_location=self.engine_location,
                                                               tail_type=self.tail_type),
                           promotes=['*'])
        self.add_subsystem('flight_controls_weight', FlightControlsWeight(), promotes=['*'])
        self.add_subsystem('landing_gear_weight', LandingGearWeight(), promotes=['*'])
        # Engine have to be computed before pylons
        self.add_subsystem('engines_weight', EngineWeight(), promotes=['*'])
        self.add_subsystem('pylons_weight', PylonsWeight(engine_location=self.engine_location),
                           promotes=['*'])
        self.add_subsystem('paint_weight', PaintWeight(), promotes=['*'])
        # Propulsion
        self.add_subsystem('fuel_lines_weight', FuelLinesWeight(), promotes=['*'])
        self.add_subsystem('unconsumables_weight', UnconsumablesWeight(), promotes=['*'])
        # Systems
        self.add_subsystem('power_systems_weight', PowerSystemsWeight(), promotes=['*'])
        self.add_subsystem('life_support_systems_weight',
                           LifeSupportSystemsWeight(ac_type=self.ac_type),
                           promotes=['*'])
        self.add_subsystem('navigation_systems_weight',
                           NavigationSystemsWeight(ac_type=self.ac_type),
                           promotes=['*'])
        self.add_subsystem('transmission_systems_weight',
                           TransmissionSystemsWeight(ac_type=self.ac_type), promotes=['*'])
        self.add_subsystem('fixed_operational_systems_weight', FixedOperationalSystemsWeight(),
                           promotes=['*'])
        self.add_subsystem('flight_kit_weight', FlightKitWeight(ac_type=self.ac_type),
                           promotes=['*'])
        # Cargo and furniture
        self.add_subsystem('cargo_configuration_weight',
                           CargoConfigurationWeight(ac_type=self.ac_type),
                           promotes=['*'])
        self.add_subsystem('passenger_seats_weight', PassengerSeatsWeight(ac_type=self.ac_type),
                           promotes=['*'])
        self.add_subsystem('food_water_weight', FoodWaterWeight(ac_type=self.ac_type),
                           promotes=['*'])
        self.add_subsystem('security_kit_weight', SecurityKitWeight(ac_type=self.ac_type),
                           promotes=['*'])
        self.add_subsystem('toilets_weight', ToiletsWeight(ac_type=self.ac_type), promotes=['*'])
        # Crew
        self.add_subsystem('crew_weight', CrewWeight(), promotes=['*'])
        self.add_subsystem('link_variables', LinkWeightVariables(), promotes=['*'])
