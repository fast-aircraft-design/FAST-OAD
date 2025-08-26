<p align="center">
  <img src="https://github.com/fast-aircraft-design/FAST-OAD/blob/master/docs/img/FAST_OAD_logo2.jpg?raw=true" alt="FAST-OAD logo" width="600">
</p>

Future Aircraft Sizing Tool - Overall Aircraft Design
===============================================================
[![image](https://img.shields.io/pypi/v/fast-oad-core.svg)](https://pypi.python.org/pypi/fast-oad-core)
[![image](https://img.shields.io/pypi/pyversions/fast-oad-core.svg)](https://pypi.python.org/pypi/fast-oad-core)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

![Tests](https://github.com/fast-aircraft-design/FAST-OAD/workflows/Tests/badge.svg)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/9691f1d1430c45cf9c94bc342b4c6122)](https://app.codacy.com/gh/fast-aircraft-design/FAST-OAD/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![codecov](https://codecov.io/gh/fast-aircraft-design/FAST-OAD/branch/master/graph/badge.svg)](https://codecov.io/gh/fast-aircraft-design/FAST-OAD)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[![Documentation Status](https://readthedocs.org/projects/fast-oad/badge/?version=stable)](https://fast-oad.readthedocs.io/)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/fast-aircraft-design/FAST-OAD.git/latest-release?urlpath=lab%2Ftree%2Fsrc%2Ffastoad%2Fnotebooks)
[![DOI](https://zenodo.org/badge/186570813.svg)](https://zenodo.org/badge/latestdoi/186570813)





FAST-OAD is a framework for performing rapid Overall Aircraft Design.

It proposes multi-disciplinary analysis and optimisation by relying on
the [OpenMDAO framework](https://openmdao.org/).

FAST-OAD allows easy switching between models for a same discipline, and
also adding/removing/developing models to match the need of your study.

More details can be found in the [official documentation](https://fast-oad.readthedocs.io/).

FAST-OAD operates using a plugin system to provide additional sizing model for different categories of aircraft. The following plugins are currently available in open-source:
+ [FAST-OAD_CS25](https://github.com/fast-aircraft-design/FAST-OAD_CS25): a plugin containing models to perform the sizing of CS-25/FAR-25 aircraft with emphasis on the SMR segment
+ [RTA](https://github.com/fast-aircraft-design/RTA): a variation of the FAST-OAD_CS25 which focuses on Regional Transport Aircraft
+ [FAST-OAD-GA](https://github.com/supaero-aircraft-design/FAST-GA): a plugin containing models for the sizing of General Aviation aircraft with conventional propulsive systems.
+ [FAST-OAD_CS23-HE](https://github.com/florentLutz/FAST-OAD-CS23-HE): a variation of FAST-OAD-GA to allow for the sizing of all- and hybrid-electric configuration.

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

Can’t find the models you need for your project? No problem, you can code them yourself! Detailed explanation on the plugin system and how to transform custom modules in a plugin can be found in [in the documentation](https://fast-oad.readthedocs.io/en/stable/documentation/custom_modules/add_plugin.html). A [GitHub template](https://github.com/fast-aircraft-design/FAST-OAD_plugin_template) with all the information you need to start developing your own FAST-OAD models is also available.

⏩ Want to try quickly?
----------------------
You can run FAST-OAD tutorials **without installation** using our
[Binder-hosted Jupyter notebooks](https://mybinder.org/v2/gh/fast-aircraft-design/FAST-OAD.git/latest-release?filepath=src%2Ffastoad%2Fnotebooks).


✈️ Install
----------

**Prerequisite**:FAST-OAD needs at least **Python 3.9.0**.

It is recommended (but not required) to install FAST-OAD in a virtual
environment ([conda](https://docs.conda.io/en/latest/),
[venv](https://docs.python.org/3.9/library/venv.html), ...)

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

✨ Contributing
---------------

Contributions are welcome! If you want to report a bug or request new features, feel free to drop an issue. For issue pertaining to the framework itself, use the following [link](https://github.com/fast-aircraft-design/FAST-OAD/issues/new/choose). For issues that have to do with the models, make sure to report it in the repository of the affected plugin. In any case, make sure to check the [recommended practices](https://github.com/fast-aircraft-design/FAST-OAD/wiki/Good-practices).