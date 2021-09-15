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

import openmdao.api as om

from fastoad.models.aerostructure.aerodynamic.external.AVL.avl import AVL
from fastoad.models.aerostructure.mesh.aerodynamic_mesh import AerodynamicMesh
from fastoad.models.aerostructure.mesh.structure_mesh import StructureMesh
from fastoad.models.aerostructure.structure.external.mystran.mystran_static import MystranStatic
from fastoad.models.aerostructure.structure.structural_weight import StructuralWeight
from fastoad.models.aerostructure.transfer.displacements_transfer import DisplacementsTransfer
from fastoad.models.aerostructure.transfer.forces_transfer import ForcesTransfer
from fastoad.models.aerostructure.transfer.transfer_matrices import TransferMatrices
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem


@RegisterOpenMDAOSystem("fastoad.aerostructure.static")
class StaticSolver(om.Group):
    def initialize(self):
        self.options.declare(
            "coupled_components",
            types=list,
            allow_none=False,
            desc="List of components considered for aerostructural loop",
        )
        self.options.declare(
            "additional_aerodynamic_components",
            types=list,
            default=[],
            desc="List of components considered for aerodynamic computations "
            "but not considered for aerostructural loop",
        )
        self.options.declare(
            "additional_structural_components",
            types=list,
            default=[],
            desc="List of components considered for structural computations "
            "but not considered for aerostructural loop",
        )
        self.options.declare(
            "aerodynamic_components_sections",
            types=list,
            allow_none=False,
            desc="List with the number of slices for each aerodynamic component",
        )
        self.options.declare(
            "structural_components_sections",
            types=list,
            allow_none=False,
            desc="List with the number of slices for each aerodynamic component",
        )
        self.options.declare(
            "coupled_components_interpolations",
            types=list,
            allow_none=False,
            desc="List of interpolation methods to be applied for each coupled component",
        )
        self.options.declare(
            "has_strut",
            types=bool,
            default=False,
            desc="True if strut-braced wing configuration should be considered",
        )
        self.options.declare(
            "has_vertical_strut",
            types=bool,
            default=False,
            desc="True if a strut-braced wing and strut composed of vertical + horizontal parts",
        )

    def setup(self):
        if (
            "strut"
            in self.options["coupled_components"]
            + self.options["additional_structural_components"]
            + self.options["additional_aerodynamic_components"]
        ):
            self.options["has_strut"] = True
        if self.options["has_vertical_strut"] and not self.options["has_strut"]:
            raise (
                ValueError(
                    "Option 'has_strut' must be True or 'strut' in components lists to use option 'has_vertical_strut'"
                )
            )

        self.add_subsystem(
            "structure_mesh",
            StructureMesh(
                structural_components=self.options["coupled_components"]
                + self.options["additional_structural_components"],
                structural_components_sections=self.options["structural_components_sections"],
            ),
            promotes=["*"],
        )
        self.add_subsystem("structural_weight", StructuralWeight(), promotes=["*"])

        self.add_subsystem(
            "aerodynamic_mesh",
            AerodynamicMesh(
                aerodynamic_components=self.options["coupled_components"]
                + self.options["additional_aerodynamic_components"],
                aerodynamic_components_sections=self.options["aerodynamic_components_sections"],
            ),
            promotes=["*"],
        )
        self.add_subsystem(
            "displacement_transfer_matrices",
            TransferMatrices(
                coupled_components=self.options["coupled_components"],
                structural_components_sections=self.options["structural_components_sections"],
                aerodynamic_components_sections=self.options["aerodynamic_components_sections"],
                coupled_components_interpolations=self.options["coupled_components_interpolations"],
            ),
            promotes=["*"],
        )

        self.add_subsystem(
            "aerostructural_loop",
            _AerostructuralLoop(
                coupled_components=self.options["coupled_components"],
                additional_aerodynamic_components=self.options["additional_aerodynamic_components"],
                additional_structural_components=self.options["additional_structural_components"],
                structural_components_sections=self.options["structural_components_sections"],
                aerodynamic_components_sections=self.options["aerodynamic_components_sections"],
            ),
            promotes=["*"],
        )

        # self.add_subsystem(
        #     "displacement_transfer2",
        #     DisplacementsTransfer(components=self.options["components"]),
        #     promotes=["*"],
        # )
        # self.add_subsystem(
        #     "Aerodynamic_solver2",
        #     AVL(
        #         components=self.options["components"],
        #         components_sections=self.options["components_sections"],
        #         coupling_iterations=False
        #     ),
        #     promotes=["*"],
        # )
        # self.add_subsystem(
        #     "Forces_transfer2",
        #     ForcesTransfer(
        #         components=self.options["components"],
        #         components_sections=self.options["components_sections"],
        #     ),
        #     promotes=["*"],
        # )
        # self.add_subsystem(
        #     "static_structure_solver2",
        #     MystranStatic(
        #         components=self.options["components"],
        #         components_sections=self.options["components_sections"],
        #         coupling_iterations=False
        #     ),
        #     promotes=["*"],
        # )


class _AerostructuralLoop(om.Group):
    def initialize(self):
        self.options.declare("coupled_components", types=list)
        self.options.declare("additional_aerodynamic_components", types=list)
        self.options.declare("additional_structural_components", types=list)
        self.options.declare("aerodynamic_components_sections", types=list)
        self.options.declare("structural_components_sections", types=list)

    def setup(self):

        self.add_subsystem(
            "Aerodynamic_solver",
            AVL(
                aerodynamic_components=self.options["coupled_components"]
                + self.options["additional_aerodynamic_components"],
                aerodynamic_components_sections=self.options["aerodynamic_components_sections"],
            ),
            promotes=["*"],
        )
        self.add_subsystem(
            "Forces_transfer",
            ForcesTransfer(
                coupled_components=self.options["coupled_components"],
                structural_components_sections=self.options["structural_components_sections"],
            ),
            promotes=["*"],
        )
        self.add_subsystem(
            "static_structure_solver",
            MystranStatic(
                structural_components=self.options["coupled_components"]
                + self.options["additional_structural_components"],
                structural_components_sections=self.options["structural_components_sections"],
            ),
            promotes=["*"],
        )

        self.add_subsystem(
            "displacement_transfer",
            DisplacementsTransfer(
                coupled_components=self.options["coupled_components"],
                aerodynamic_components_sections=self.options["aerodynamic_components_sections"],
            ),
            promotes=["*"],
        )

        self.nonlinear_solver = om.NonlinearBlockGS(
            maxiter=20, iprint=1, rtol=1e-4, atol=1e-8, use_aitken=True
        )
        self.linear_solver = om.DirectSolver()
