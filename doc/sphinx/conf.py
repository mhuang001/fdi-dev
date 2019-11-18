# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import sphinx_rtd_theme
import aiohttp_theme

sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = 'spdc'
copyright = '2019, Maohai Huang'
author = 'Maohai Huang'

# The full version, including alpha/beta/rc tags
release = 'v0.8'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc']
extensions.append("sphinx_rtd_theme")

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '*~']


# -- Options for HTML output -------------------------------------------------

# https://stackoverflow.com/a/32079202
# def setup(app):
#    app.add_css_file("hatnotes.css")
# app.add_css_file("aiohttp1.css")


# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#html_theme = 'alabaster'
#html_theme = 'sphinxdoc'
#html_theme = "sphinx_rtd_theme"
html_theme = "aiohttp_theme"

# Alabaster side bar
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'searchbox.html',
        'donate.html',
    ]
}

#from os import path
# def xsetup(app):
#    app.add_html_theme('aiohttp_theme', path.abspath(path.dirname(__file__)))


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# The following are from readthedocs.org
# https://docs.readthedocs.io/en/stable/guides/adding-custom-css.html

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    'css/custom.css',
]

html_js_files = [
    'js/custom.js',
]

#html_style = 'css/yourtheme.css'
