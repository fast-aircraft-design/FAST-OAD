from numpy.testing import assert_allclose

from fastoad._utils.sellar.sellar_base import BasicSellarModel, BasicSellarProblem


def test_sellar():
    problem = BasicSellarProblem(BasicSellarModel())

    problem.setup()
    problem.run_driver()
    assert_allclose(problem["f"], 3.183393951729169)
