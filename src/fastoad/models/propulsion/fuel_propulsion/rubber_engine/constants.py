"""
Constants for rubber engine analytical models
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

from stdatm import AtmosphereSI

RUBBER_ENGINE_DESCRIPTION = """
Parametric engine model as OpenMDAO component.

Implementation of E. Roux models for fuel consumption of low bypass ratio engines
For more information, see RubberEngine class in FAST-OAD developer documentation.
"""

# Atmosphere at limits of troposhere
ATM_SEA_LEVEL = AtmosphereSI(0)
ATM_TROPOPAUSE = AtmosphereSI(11000)

# Constants for computation of maximum thrust ---------------------------------
# (see E. Roux model definition in roux:2005)
A_MS = -2.74e-4
A_FM = 2.67e-4
B_MS = 1.91e-2
B_FM = -2.35e-2
C_MS = 1.21e-3
C_FM = -1.32e-3
D_MS = -8.48e-4
D_FM = 3.14e-4
E_MS = 8.96e-1
E_FM = 5.22e-1

ALPHA = [
    [1.79e-12, 4.29e-13, -5.24e-14, -4.51e-14, -4.57e-12],
    [1.17e-8, -8.80e-8, -5.25e-9, -3.19e-9, 5.52e-8],
    [-5.37e-13, -1.26e-12, 1.29e-14, 2.39e-14, 2.35e-12],
    [-3.18e-9, 2.76e-8, 1.97e-9, 1.17e-9, -2.26e-8],
]

BETA = [
    [1.70e-12, 1.51e-12, 1.48e-9, -7.59e-14, -1.07e-11],
    [-3.48e-9, -8.41e-8, 2.56e-5, -2.00e-8, -7.17e-8],
    [-3.89e-13, -2.05e-12, -9.28e-10, 1.30e-13, 5.39e-12],
    [1.77e-9, 2.62e-8, -8.87e-6, 6.66e-9, 4.43e-8],
]
# -----------------------------------------------------------------------------

# Constants for computation of SFC ratio --------------------------------------
MAX_SFC_RATIO_COEFF = 0.5
# -----------------------------------------------------------------------------
