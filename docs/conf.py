# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Path setup
import os
import sys
sys.path.insert(0, os.path.abspath("../src"))

# Project information
project = "NAGUS"
copyright = '2022, dgelessus, <a href="http://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>'
author = "dgelessus"

# General configuration
extensions = [
	"sphinx.ext.autodoc",
]
templates_path = ["_templates"]
exclude_patterns = [
	"_build",
	"Thumbs.db",
	".DS_Store",
]

# Options for HTML output
html_static_path = ["_static"]
