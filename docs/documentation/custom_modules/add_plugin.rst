.. _add-plugin:

##########################################################
How to add custom OpenMDAO modules to FAST-OAD as a plugin
##########################################################

Once you have created your custom modules for FAST-OAD (see :ref:`add-modules`),
you may want to share them with other users, which can be done in two ways:

    - Providing your code so they can copy it on their computer and have them set their
      :code:`custom_modules` field accordingly in their :ref:`configuration-file`.
    - Packaging your code as a FAST-OAD plugin and have them install it through :code:`pip`
      or equivalent.

To declare your custom modules as a FAST-OAD plugin, you have to package them the usual way
and declare them as a plugin with :code:`fastoad_model` as plugin group name.

This can be done classically with `setuptools <https://packaging.python.org/guides/creating-and-discovering-plugins/#using-package-metadata>`_.
It can also be done with `Poetry <https://python-poetry.org>`_, which is the way described below:

.. contents::
   :local:
   :depth: 1


******************************
Plugin declaration
******************************

Assuming you project contains the package :code:`start_trek.drives` that contains
models you want to share, you can declare your plugin in your :code:`pyproject.toml`
file with:

.. code-block:: toml

    ...

    [tool.poetry.plugins."fastoad_model"]
    "internal_models" = "start_trek.drives"

    ...
Once your :code:`pyproject.toml` is set, you can do :code:`poetry install`. Besides
installing your project dependencies, it will make your models **locally** available (i.e.
you could use their identifiers in your FAST-OAD configuration file without setting
the :code:`custom_modules` field)


******************************
Building
******************************
You can build your package with the command line :code:`poetry build`.
Let's assume your :code:`pyproject.toml` file is configured so that your project name is
:code:`STST_drive_models`, as below:

.. code-block:: toml

    ...

    [tool.poetry]
    name = "ST_drive_models"
    version = "1.0.0"

    ...

It will create a :code:`dist` folder with two files: :code:`ST_drive_models-1.0.0.tar.gz`
and :code:`ST_drive_models-1.0.0-py3-none-any.whl` (or something like this).

You may then have sent any of those two files to another user, who may then install your models
using :code:`pip` with:

.. code-block:: shell-session

    $ pip install ST_drive_models-1.0.0-py3-none-any.whl  # or ST_drive_models-1.0.0.tar.gz

******************************
Publishing
******************************
Once you have built your package, you may publish it on a a package repository.
:code:`poetry publish` will publish your package on `PyPI <https://pypi.org>`_,
provided that you have correctly set your account.

Poetry can also publish to another destination.

Please see `here <https://python-poetry.org/docs/cli/#publish>`_ for detailed information.

