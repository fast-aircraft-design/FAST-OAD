"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""
from openmdao.api import Group

from fastoad.modules.geometry.geom_components.fuselage.compute_fuselage \
    import ComputeFuselageGeometryBasic, ComputeFuselageGeometryCabinSizing
from fastoad.modules.geometry.geom_components.wing.compute_wing import ComputeWingGeometry
from fastoad.modules.geometry.geom_components.nacelle_pylons.compute_nacelle_pylons import \
    ComputeNacelleAndPylonsGeometry
from fastoad.modules.geometry.get_cg import GetCG
from fastoad.modules.geometry.cg_components.compute_aero_center import ComputeAeroCenter
from fastoad.modules.geometry.cg_components.compute_static_margin import ComputeStaticMargin

from fastoad.modules.geometry.options import AIRCRAFT_FAMILY_OPTION, \
    TAIL_TYPE_OPTION, ENGINE_LOCATION_OPTION, AIRCRAFT_TYPE_OPTION, CABIN_SIZING_OPTION


class Geometry(Group):
    """ Overall geometry model """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

        self.options.declare(ENGINE_LOCATION_OPTION, types=float, default=1.0)
        self.options.declare(TAIL_TYPE_OPTION, types=float, default=0.0)
        self.options.declare(AIRCRAFT_FAMILY_OPTION, types=float, default=1.0)
        self.options.declare(AIRCRAFT_TYPE_OPTION, types=float, default=2.0)
        self.options.declare(CABIN_SIZING_OPTION, types=float, default=1.0)

        self.engine_location = self.options[ENGINE_LOCATION_OPTION]
        self.tail_type = self.options[TAIL_TYPE_OPTION]
        self.ac_family = self.options[AIRCRAFT_FAMILY_OPTION]
        self.ac_type = self.options[AIRCRAFT_TYPE_OPTION]
        self.cabin_sizing = self.options[CABIN_SIZING_OPTION]

    def setup(self):
        deriv_method = self.options['deriv_method']

        if self.cabin_sizing == 1.0:
            self.add_subsystem('compute_fuselage',
                               ComputeFuselageGeometryCabinSizing(deriv_method=deriv_method),
                               promotes=['*'])
        else:
            self.add_subsystem('compute_fuselage',
                               ComputeFuselageGeometryBasic(deriv_method=deriv_method),
                               promotes=['*'])

        self.add_subsystem('compute_wing',
                           ComputeWingGeometry(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('compute_engine_nacelle',
                           ComputeNacelleAndPylonsGeometry(engine_location=self.engine_location,
                                                           ac_family=self.ac_family,
                                                           deriv_method=deriv_method),
                           promotes=['*'])
        self.add_subsystem('get_cg', GetCG(engine_location=self.engine_location,
                                           tail_type=self.tail_type,
                                           ac_family=self.ac_family,
                                           ac_type=self.ac_type,
                                           deriv_method=deriv_method),
                           promotes=['*'])
        self.add_subsystem('compute_aero_center',
                           ComputeAeroCenter(deriv_method=deriv_method), promotes=['*'])
        self.add_subsystem('compute_sm',
                           ComputeStaticMargin(deriv_method=deriv_method), promotes=['*'])
