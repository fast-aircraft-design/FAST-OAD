# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

# -- Run sphinx-apidoc ------------------------------------------------------
try:  # for Sphinx >= 1.7
    from sphinx.ext import apidoc
except ImportError:
    from sphinx import apidoc


def run_apidoc(_):
    import os
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    output_dir = os.path.join(cur_dir, "api")
    module = os.path.join(cur_dir, "..", "src", "fastoad")
    apidoc.main(
        ["-d", "1", "-e", "-o", output_dir, module, "--force",]
    )


def setup(app):
    app.connect("builder-inited", run_apidoc)


# -- Project information -----------------------------------------------------

project = "FAST-OAD"
copyright = "2020, ONERA @ ISAE-SUPAERO"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.viewcode",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.ifconfig",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinxcontrib.bibtex",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "api/*.tests.*", "api/*.resources.rst"]

# Use docstring from class and __init__
autoclass_content = "both"

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

try:
    from fastoad import __version__
except ImportError:
    pass
else:
    release = version = __version__


# -- External mapping ------------------------------------------------------------
python_version = ".".join(map(str, sys.version_info[0:2]))
intersphinx_mapping = {
    "sphinx": ("http://www.sphinx-doc.org/en/stable", None),
    "python": ("https://docs.python.org/" + python_version, None),
    "matplotlib": ("https://matplotlib.org", None),
    "numpy": ("https://docs.scipy.org/doc/numpy", None),
    "sklearn": ("http://scikit-learn.org/stable", None),
    "pandas": ("http://pandas.pydata.org/pandas-docs/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
}
