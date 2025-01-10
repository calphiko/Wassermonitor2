# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath("../../Server/API/"))
sys.path.insert(0, os.path.abspath("../../Pi/"))
sys.path.insert(0, os.path.abspath("../../Server/Warningbot/"))
print(sys.path)

project = 'Wassermonitor2'
copyright = '2024, 2025, Carl Philipp Koppen'
author = 'Carl Philipp Koppen'

html_favicon = '_static/favicon.png'
html_logo = '_static/favicon.png'
html_static_path = ['_static']

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # Falls Sie Google- oder NumPy-Style-Docstrings verwenden
    "sphinx.ext.viewcode",  # Fügt Links zum Quellcode hinzu
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
