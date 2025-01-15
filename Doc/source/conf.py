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

version = 'unknown'  # Standardwert, wird durch den Workflow überschrieben
release = 'unknown release'  # Standardwert, wird durch den Workflow überschrieben

html_favicon = '_static/favicon.png'
html_logo = '_static/favicon.png'
html_static_path = ['_static']

# -- HTML output options ------------------------------------------------------

html_title = f'{project} {version}'  # Zeigt die Version im Dokumentationstitel an

# Anzeige der Version im Footer oder Untertitel
html_context = {
    "display_github": True,
    "github_user": "DeinGitHubName",
    "github_repo": "DeinRepository",
    "github_version": "main",  # Branch, der für die Dokumentation verwendet wird
    "conf_py_path": "/docs/",
    "version": version,  # Diese Version wird durch den Workflow gesetzt
}


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
