"""
Estimation of wing geometry (components)
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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
from .compute_b_50 import ComputeB50
from .compute_cl_alpha import ComputeCLalpha
from .compute_l1_l4 import ComputeL1AndL4Wing
from .compute_l2_l3 import ComputeL2AndL3Wing
from .compute_mac_wing import ComputeMACWing
from .compute_mfw import ComputeMFW
from .compute_sweep_wing import ComputeSweepWing
from .compute_toc_wing import ComputeToCWing
from .compute_wet_area_wing import ComputeWetAreaWing
from .compute_x_wing import ComputeXWing
from .compute_y_wing import ComputeYWing

# TODO: Determine wether wing drawing shall be included or not
# from .wing_drawing import WingDrawing
