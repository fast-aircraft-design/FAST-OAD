.. _installation-procedure:

######################
Installation procedure
######################
**Prerequisite**:FAST-OAD needs at least **Python 3.6.1** (usage of **Python 3.8.*** is discouraged as Jupyter notebooks are still `not compatible with it <https://github.com/jupyterlab/jupyterlab/issues/6487>`_).

It is recommended (but not required) to install FAST-OAD in a virtual environment (`conda <https://docs.conda.io/en/latest/>`_, `venv <https://docs.python.org/3.7/library/venv.html>`_...)

Once Python is installed, FAST-OAD can be installed using pip.

    **Note**: If your network uses a proxy, you may have to do `some settings <https://pip.pypa.io/en/stable/user_guide/#using-a-proxy-server>`_ for pip to work correctly

Until FAST-OAD is publicly released, the installation process must rely on GitHub
instead of PyPI. Therefore, you have 2 ways to install it:

******************
With Git installed
******************
You can install the latest version with this command:

.. code:: bash

    $ pip install -e git+https://github.com/fast-aircraft-design/FAST-OAD.git

At the prompt, enter your GitHub credentials.

*********************
Without Git installed
*********************
Please download this tarball: `<https://github.com/fast-aircraft-design/FAST-OAD/archive/master.zip>`_

Unzip it in the location of your choice, then do:

.. code:: bash

   $ pip install -e <location/of/FAST-OAD-latest/>

