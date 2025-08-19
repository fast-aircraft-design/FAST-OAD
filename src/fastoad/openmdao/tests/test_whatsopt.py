import shutil
from pathlib import Path

import pytest

from .openmdao_sellar_example.sellar import SellarModel
from ..problem import FASTOADProblem
from ..whatsopt import write_xdsm

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results" / Path(__file__).stem


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    RESULTS_FOLDER_PATH.mkdir(parents=True)


@pytest.mark.skip(
    reason="Using web access during tests should not be the default behavior. "
    "Moreover, fastoad/cmd/tests/test_apy.py:test_write_xdsm does a similar test."
)
def test_write_xdsm(cleanup):
    problem = FASTOADProblem()
    problem.model.add_subsystem("sellar", SellarModel(), promotes=["*"])
    problem.output_file_path = RESULTS_FOLDER_PATH / "output.xml"
    problem.setup()
    problem.final_setup()

    xdsm_file_path = RESULTS_FOLDER_PATH / "xdsm.html"
    write_xdsm(problem, xdsm_file_path, dry_run=True)
    assert xdsm_file_path.joinpath()
