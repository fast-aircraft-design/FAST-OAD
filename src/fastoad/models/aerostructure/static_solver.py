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

from fastoad.models.aerostructure.mesh.structure_mesh import StructureMesh
from fastoad.models.aerostructure.mesh.aerodynamic_mesh import AerodynamicMesh
from fastoad.models.aerostructure.transfer.transfer_matrices import TransferMatrices
from fastoad.models.aerostructure.transfer.displacements_transfer import DisplacementsTransfer
from fastoad.models.aerostructure.transfer.forces_transfer import ForcesTransfer
from fastoad.models.aerostructure.structure.external.mystran.mystran_static import MystranStatic
from fastoad.models.aerostructure.aerodynamic.external.AVL.avl import AVL
from fastoad.models.options import OpenMdaoOptionDispatcherGroup as OmOptGrp


class StaticSolver(OmOptGrp):
    def initialize(self):
        self.options.declare("components", types=list)
        self.options.declare("components_sections", types=list)
        self.options.declare("components_interp", types=list)

    def setup(self):
        self.add_subsystem(
            "structure_mesh",
            StructureMesh(
                components=self.options["components"],
                components_sections=self.options["components_sections"],
            ),
            promotes=["*"],
        )
        self.add_subsystem(
            "aerodynamic_mesh",
            AerodynamicMesh(
                components=self.options["components"],
                components_sections=self.options["components_sections"],
            ),
            promotes=["*"],
        )
        self.add_subsystem(
            "displacement_transfer_matrices",
            TransferMatrices(
                components=self.options["components"],
                components_sections=self.options["components_sections"],
                components_interp=self.options["components_interp"],
            ),
            promotes=["*"],
        )

        self.add_subsystem(
            "aerostructural_loop",
            _AerostructuralLoop(
                components=self.options["components"],
                components_sections=self.options["components_sections"],
                components_interp=self.options["components_interp"],
            ),
            promotes=["*"],
        )
        # self.add_subsystem(
        #     "displacement_transfer",
        #     DisplacementsTransfer(components=self.options["components"]),
        #     promotes=["*"],
        # )
        # self.add_subsystem(
        #     "Aerodynamic_solver",
        #     AVL(
        #         components=self.options["components"],
        #         components_sections=self.options["components_sections"],
        #     ),
        #     promotes=["*"],
        # )
        # self.add_subsystem(
        #     "Forces_transfer",
        #     ForcesTransfer(
        #         components=self.options["components"],
        #         components_sections=self.options["components_sections"],
        #     ),
        #     promotes=["*"],
        # )
        # self.add_subsystem(
        #     "static_structure_solver",
        #     MystranStatic(
        #         components=self.options["components"],
        #         components_sections=self.options["components_sections"],
        #     ),
        #     promotes=["*"],
        # )


class _AerostructuralLoop(OmOptGrp):
    def initialize(self):
        self.options.declare("components", types=list)
        self.options.declare("components_sections", types=list)
        self.options.declare("components_interp", types=list)

    def setup(self):

        self.add_subsystem(
            "Aerodynamic_solver",
            AVL(
                components=self.options["components"],
                components_sections=self.options["components_sections"],
            ),
            promotes=["*"],
        )
        self.add_subsystem(
            "Forces_transfer",
            ForcesTransfer(
                components=self.options["components"],
                components_sections=self.options["components_sections"],
            ),
            promotes=["*"],
        )
        self.add_subsystem(
            "static_structure_solver",
            MystranStatic(
                components=self.options["components"],
                components_sections=self.options["components_sections"],
            ),
            promotes=["*"],
        )

        self.add_subsystem(
            "displacement_transfer",
            DisplacementsTransfer(components=self.options["components"]),
            promotes=["*"],
        )

        self.nonlinear_solver = om.NonlinearBlockGS(maxiter=30, iprint=1, rtol=1e-3, atol=1e-9)
        self.linear_solver = om.DirectSolver()
