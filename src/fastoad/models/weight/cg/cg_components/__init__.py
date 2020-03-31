"""
Estimation of centers of gravity
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

from .compute_cg_control_surfaces import ComputeControlSurfacesCG
from .compute_cg_loadcase1 import ComputeCGLoadCase1
from .compute_cg_loadcase2 import ComputeCGLoadCase2
from .compute_cg_loadcase3 import ComputeCGLoadCase3
from .compute_cg_loadcase4 import ComputeCGLoadCase4
from .compute_cg_others import ComputeOthersCG
from .compute_cg_ratio_aft import ComputeCGRatioAft
from .compute_cg_tanks import ComputeTanksCG
from .compute_cg_wing import ComputeWingCG
from .compute_global_cg import ComputeGlobalCG
from .compute_ht_cg import ComputeHTcg
from .compute_max_cg_ratio import ComputeMaxCGratio
from .compute_vt_cg import ComputeVTcg
from .update_mlg import UpdateMLG
