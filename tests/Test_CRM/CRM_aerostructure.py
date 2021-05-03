import os.path as pth
import openmdao.api as om
from fastoad import api
from fastoad.models.aerostructure.static_solver import StaticSolver
import logging
import shutil


DATA_FOLDER_PATH = "data"
WORKDIR_FOLDER_PATH = "workdir"

# api.generate_configuration_file(pth.join(DATA_FOLDER_PATH, "ref.toml"))
input_file = api.generate_inputs(pth.join(DATA_FOLDER_PATH, "config.toml"), overwrite=True)

# problem = om.Problem()
# model = om.Group()
# model.add_subsystem(
#     "aerostruct",
#     StaticSolver(components=["wing"], components_sections=[5], components_interp=["linear"]),
#     promotes=["*"],
# )