![Tests](https://github.com/fast-aircraft-design/FAST-OAD/workflows/Tests/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/fast-oad/badge/?version=latest)](https://fast-oad.readthedocs.io/en/latest/?badge=latest)

FAST-OAD: Future Aircraft Sizing Tool - Overall Aircraft Design
===============================================================

FAST-OAD is a framework for performing rapid Overall Aircraft Design.

It proposes multi-disciplinary analysis and optimisation by relying on
the [OpenMDAO framework](https://openmdao.org/).

FAST-OAD allows easy switching between models for a same discipline, and
also adding/removing disciplines to match the need of your study.

Currently, FAST-OAD is bundled with models for commercial transport
aircraft of years 1990-2000. Other models will come and you may create
your own models and use them instead of bundled ones.

More details can be found in the [official
documentation](https://fast-aircraft-design.github.io/FAST-OAD-doc/).

Install
-------

**Prerequisite**:FAST-OAD needs at least **Python 3.6.1** (usage of
**Python 3.8.**\* is discouraged as Jupyter notebooks are still [not
compatible with
it](https://github.com/jupyterlab/jupyterlab/issues/6487)).

It is recommended (but not required) to install FAST-OAD in a virtual
environment ([conda](https://docs.conda.io/en/latest/),
[venv](https://docs.python.org/3.7/library/venv.html), ...)

Once Python is installed, FAST-OAD can be installed using pip.

> **Note**: If your network uses a proxy, you may have to do [some
> settings](https://pip.pypa.io/en/stable/user_guide/#using-a-proxy-server)
> for pip to work correctly

You can install the latest version with this command:

``` {.bash}
$ pip install --upgrade FAST-OAD
```
