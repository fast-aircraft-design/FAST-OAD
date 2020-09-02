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

import numpy as np
import openmdao
import openmdao.api as om
from packaging import version

from fastoad.openmdao.utils import get_problem_after_setup


def set_all_input_defaults(model: om.Group):
    """
    Sets needed defaults to avoid error messages about ambiguous variable definitions.

    Does nothing if OpenMDAO version is below 3.2.

    :param model: the model where defaults will be added in place.
    """
    # FIXME: This solution is a patch to get compatible with OpenMDAO 3.2 but it not really
    #  satisfactory because it does not help in case of custom models using existing variables
    #  with different units.
    #  Maybe a future evolution of OpenMDAO will open the way to a better solution...

    if version.parse(openmdao.__version__) < version.parse("3.2"):
        return

    variables = {
        "data:geometry:wing:sweep_25": dict(val=np.nan, units="deg"),
        "data:TLAR:range": dict(val=np.nan, units="NM"),
    }

    # Defaults must be added only if variable is present. Otherwise, an error is raised at setup().
    # Therefore, a setup() is done and if OpenMDAO complains about missing default and if that
    # default is available, it is added.
    ok = False
    while not ok and len(variables) > 0:  # Stops if no error or if no default definition is left.
        try:
            get_problem_after_setup(om.Problem(model))
            ok = True
        except RuntimeError as exc:
            var_default_has_been_set = False
            for var_name, metadata in variables.items():
                if var_name in exc.args[0]:
                    model.set_input_defaults(var_name, **metadata)
                    var_default_has_been_set = True
                    break
            if var_default_has_been_set:
                del variables[var_name]
