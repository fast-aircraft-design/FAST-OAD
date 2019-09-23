"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""
from openmdao.api import Group, NonlinearBlockGS, LinearBlockGS

from fastoad.modules.geometry.geom_components.ht \
    import ComputeHorizontalTailGeometry
from fastoad.modules.geometry.geom_components.vt.compute_vertical_tail \
    import ComputeVerticalTailGeometry
from fastoad.modules.geometry.geom_components.update_mlg \
    import UpdateMLG
from fastoad.modules.geometry.geom_components.compute_total_area \
    import ComputeTotalArea
from fastoad.modules.geometry.cg_components.compute_global_cg \
    import ComputeGlobalCG
from fastoad.modules.geometry.cg_components.compute_cg_control_surfaces \
    import ComputeControlSurfacesCG
from fastoad.modules.geometry.cg_components.compute_cg_wing \
    import ComputeWingCG
from fastoad.modules.geometry.cg_components.compute_cg_tanks \
    import ComputeTanksCG
from fastoad.modules.geometry.cg_components.compute_cg_others \
    import ComputeOthersCG
from fastoad.modules.mass_breakdown.mass_breakdown \
    import MassBreakdown


class GetCG(Group):
    """ Model that computes the global center of gravity """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

        self.options.declare('engine_location', types=float, default=1.0)
        self.options.declare('tail_type', types=float, default=0.0)
        self.options.declare('ac_family', types=float, default=1.0)
        self.options.declare('ac_type', types=float, default=2.0)

        self.engine_location = self.options['engine_location']
        self.tail_type = self.options['tail_type']
        self.ac_family = self.options['ac_family']
        self.ac_type = self.options['ac_type']

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_subsystem('compute_ht',
                           ComputeHorizontalTailGeometry(ac_family=self.ac_family,
                                                         tail_type=self.tail_type,
                                                         deriv_method=deriv_method),
                           promotes=['*'])
        self.add_subsystem('compute_vt',
                           ComputeVerticalTailGeometry(ac_family=self.ac_family,
                                                       tail_type=self.tail_type,
                                                       deriv_method=deriv_method),
                           promotes=['*'])
        self.add_subsystem('compute_total_area',
                           ComputeTotalArea(deriv_method=deriv_method),
                           promotes=['*'])
        # TODO: Add deriv option to mass breakdown
        self.add_subsystem('compute_mass_breakdown',
                           MassBreakdown(engine_location=self.engine_location,
                                         tail_type=self.tail_type,
                                         ac_type=self.ac_type),
                           promotes=['*'])
        self.add_subsystem('compute_cg_wing',
                           ComputeWingCG(deriv_method=deriv_method),
                           promotes=['*'])
        self.add_subsystem('compute_cg_control_surface',
                           ComputeControlSurfacesCG(deriv_method=deriv_method),
                           promotes=['*'])
        self.add_subsystem('compute_cg_tanks',
                           ComputeTanksCG(), promotes=['*'])
        self.add_subsystem('compute_cg_others',
                           ComputeOthersCG(deriv_method=deriv_method),
                           promotes=['*'])
        self.add_subsystem('compute_cg',
                           ComputeGlobalCG(deriv_method=deriv_method),
                           promotes=['*'])
        self.add_subsystem('update_mlg',
                           UpdateMLG(deriv_method=deriv_method),
                           promotes=['*'])

        # Solvers setup
        self.nonlinear_solver = NonlinearBlockGS()
        self.nonlinear_solver.options['iprint'] = 0
        self.nonlinear_solver.options['maxiter'] = 50
        self.linear_solver = LinearBlockGS()
        self.linear_solver.options['iprint'] = 0
