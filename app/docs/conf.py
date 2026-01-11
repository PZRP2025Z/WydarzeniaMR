# Configuration file for the Sphinx documentation builder.
# Full list of options: https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Project information -----------------------------------------------------
project = "WydarzeniaMR"
copyright = "2026, Błażej Michalak, Wojciech Sarwiński, Maciej Scheffer"
author = "Błażej Michalak, Wojciech Sarwiński, Maciej Scheffer"

# -- Path setup ---------------------------------------------------------------
sys.path.insert(0, os.path.abspath(".."))  # aby Sphinx znalazł Twój app

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",  # generowanie dokumentacji z docstringów
    "sphinx.ext.napoleon",  # obsługuje Google/Doxygen docstrings
    "sphinx.ext.viewcode",  # link do źródeł w HTML
]

# W razie problemów z importem modułów, można zamockować
autodoc_mock_imports = ["app.main"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- HTML output options -----------------------------------------------------
html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "navigation_depth": 4,  # ile poziomów w bocznym menu
    "collapse_navigation": False,
    "titles_only": False,
}

# Ścieżka do statycznych plików (CSS, obrazy)
html_static_path = ["_static"]

# Logo i favicon (opcjonalnie)
# html_logo = "_static/logo.png"
# html_favicon = "_static/favicon.ico"

# Dodatkowy CSS jeśli chcesz własne style
# html_css_files = [
#     "custom.css",
# ]
