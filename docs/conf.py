# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Path setup
import os
import sys
sys.path.insert(0, os.path.abspath("../src"))

# Project information
project = "NAGUS"
copyright = '2022, dgelessus, CC BY-SA 4.0'
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
