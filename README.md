<p align="center">
  <img src="docs/img/FAST_OAD_logo2.jpg" alt="FAST-OAD logo" width="600">
</p>

Future Aircraft Sizing Tool - Overall Aircraft Design
===============================================================

![Tests](https://github.com/fast-aircraft-design/FAST-OAD/workflows/Tests/badge.svg)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/9691f1d1430c45cf9c94bc342b4c6122)](https://app.codacy.com/gh/fast-aircraft-design/FAST-OAD/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![codecov](https://codecov.io/gh/fast-aircraft-design/FAST-OAD/branch/master/graph/badge.svg)](https://codecov.io/gh/fast-aircraft-design/FAST-OAD)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

[![Documentation Status](https://readthedocs.org/projects/fast-oad/badge/?version=stable)](https://fast-oad.readthedocs.io/)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/fast-aircraft-design/FAST-OAD.git/latest-release?urlpath=lab%2Ftree%2Fsrc%2Ffastoad%2Fnotebooks)
[![DOI](https://zenodo.org/badge/186570813.svg)](https://zenodo.org/badge/latestdoi/186570813)





FAST-OAD is a framework for performing rapid Overall Aircraft Design.

It proposes multi-disciplinary analysis and optimisation by relying on
the [OpenMDAO framework](https://openmdao.org/).

FAST-OAD allows easy switching between models for a same discipline, and
also adding/removing/developing models to match the need of your study.

More details can be found in the [official documentation](https://fast-oad.readthedocs.io/).

> **Important notice:**
>
> Since version 1.3.0, FAST-OAD models for commercial transport aircraft have moved in 
> package  
> [FAST-OAD-CS25](https://pypi.org/project/fast-oad-cs25/). This package is installed along with 
> FAST-OAD, to keep backward compatibility.
> 
> Keep in mind that any update of these models will now come through new releases of FAST-OAD-CS25.
> 
> To get FAST-OAD without these models, you may install
> [FAST-OAD-core](https://pypi.org/project/fast-oad-core/).
> 
> :warning: Upgrading from an earlier version than 1.3 may break the `fastoad` command line (no 
> impact on PythonAPI). See [this issue](https://github.com/fast-aircraft-design/FAST-OAD/issues/425)
> for details and fix.

Want to try quickly?
--------------------
You can run FAST-OAD tutorials **without installation** using our
[Binder-hosted Jupyter notebooks](https://mybinder.org/v2/gh/fast-aircraft-design/FAST-OAD.git/latest-release?filepath=src%2Ffastoad%2Fnotebooks).


Install
-------

**Prerequisite**:FAST-OAD needs at least **Python 3.8.0**.

It is recommended (but not required) to install FAST-OAD in a virtual
environment ([conda](https://docs.conda.io/en/latest/),
[venv](https://docs.python.org/3.7/library/venv.html), ...)

Once Python is installed, FAST-OAD can be installed using pip.

> **Note**: If your network uses a proxy, you may have to do [some
> settings](https://pip.pypa.io/en/stable/user_guide/#using-a-proxy-server)
> for pip to work correctly

You can install the latest version with this command:

``` {.bash}
$ pip install --upgrade fast-oad
```

or, if you want the minimum installation without the CS25-related models:

``` {.bash}
$ pip install --upgrade fast-oad-core
```
