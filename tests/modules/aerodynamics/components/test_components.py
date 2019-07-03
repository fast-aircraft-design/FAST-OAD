"""
test module for modules in aerodynamics/components
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

def test_high_lift_aero():
    """ Tests high_lift_aero.py """
    input_list = ['geometry:wing_area',
                  'geometry:wing_span',
                  'geometry:wing_toc_root',
                  'geometry:wing_toc_kink',
                  'geometry:wing_toc_tip',
                  'geometry:wing_l2',
                  'geometry:wing_sweep_25',
                  'geometry:wing_area_pf',
                  'weight:MTOW',
                  'weight:MLW',
                  'kfactors_a1:K_A1',
                  'kfactors_a1:offset_A1',
                  'kfactors_a1:K_A11',
                  'kfactors_a1:offset_A11',
                  'kfactors_a1:K_A12',
                  'kfactors_a1:offset_A12',
                  'kfactors_a1:K_A13',
                  'kfactors_a1:offset_A13',
                  'kfactors_a1:K_A14',
                  'kfactors_a1:offset_A14',
                  'kfactors_a1:K_A15',
                  'kfactors_a1:offset_A15',
                  'kfactors_a1:K_voil',
                  'kfactors_a1:K_mvo']

    ivc = get_indep_var_comp(input_list)
    ivc.add_output('n1m1', 241000, units='kg')
    ivc.add_output('n2m2', 250000, units='kg')

    problem = run_system(WingWeight(), ivc)

    val = problem['weight_airframe:A1']
    assert val == pytest.approx(7681, abs=1)
