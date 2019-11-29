"""
    Estimation of horizontal tail chords and span
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
import math
import numpy as np

from openmdao.core.explicitcomponent import ExplicitComponent


# TODO: is an OpenMDAO component required for this simple calculation ?
class ComputeHTChord(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Horizontal tail chords and span estimation """

    def setup(self):

        self.add_input('geometry:horizontal_tail:aspect_ratio', val=np.nan)
        self.add_input('geometry:horizontal_tail:area', val=np.nan, units='m**2')
        self.add_input('geometry:horizontal_tail:taper_ratio', val=np.nan)

        self.add_output('geometry:horizontal_tail:span', units='m')
        self.add_output('geometry:horizontal_tail:root_chord', units='m')
        self.add_output('geometry:horizontal_tail:tip_chord', units='m')

        self.declare_partials('geometry:horizontal_tail:span',
                              ['geometry:horizontal_tail:area', 'geometry:horizontal_tail:aspect_ratio'],
                              method='fd')
        self.declare_partials('geometry:horizontal_tail:root_chord', '*', method='fd')
        self.declare_partials('geometry:horizontal_tail:tip_chord', '*', method='fd')

    def compute(self, inputs, outputs):
        lambda_ht = inputs['geometry:horizontal_tail:aspect_ratio']
        s_h = inputs['geometry:horizontal_tail:area']
        taper_ht = inputs['geometry:horizontal_tail:taper_ratio']

        b_h = math.sqrt(lambda_ht * s_h)
        root_chord = s_h * 2 / (1 + taper_ht) / b_h
        tip_chord = root_chord * taper_ht

        outputs['geometry:horizontal_tail:span'] = b_h
        outputs['geometry:horizontal_tail:root_chord'] = root_chord
        outputs['geometry:horizontal_tail:tip_chord'] = tip_chord
