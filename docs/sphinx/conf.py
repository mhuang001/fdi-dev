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
from datetime import datetime
import sphinx_rtd_theme
#import sphinx_readable_theme
#import sphinx_bootstrap_theme

sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'fdi'
year = datetime.now().year
copyright = '2019 - %d Maohai Huang, NAOC, ESA' % year
author = 'Maohai Huang'

# The full version, including alpha/beta/rc tags
# Version info -- read without importing
# https://github.com/aio-libs/aiohttp-theme/blob/master/setup.py
_locals = {}
with open('../../fdi/_version.py') as fp:
    exec(fp.read(), None, _locals)
release = _locals['__version__']


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc']
extensions.append("sphinx_rtd_theme")
extensions.append('sphinx_copybutton')
extensions.append('sphinx.ext.napoleon')
extensions.append('sphinx.ext.inheritance_diagram')
extensions.append('sphinx.ext.viewcode')
# extensions.append(['IPython.sphinxext.ipython_console_highlighting',
#              'IPython.sphinxext.ipython_directive'])
# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '*~']


# -- Options for HTML output -------------------------------------------------

# https://stackoverflow.com/a/32079202
def setup(app):
    # app.add_css_file("hatnotes.css")
    # app.add_css_file("custom.css")
    # app.add_css_file("bootstrap.css")
    # app.add_css_file("nature.css")
    # app.add_css_file('fdi.css')
    pass


if 1:
    #from monokaimod import MonokaiMod
    pygments_style = 'fdi.utils.monokaimod.MonokaiMod'  # 'monokaimod'
else:
    pygments_style = 'monokai'

autoclass_content = 'both'
autodoc_inherit_docstrings = True

napoleon_google_docstring = False
napoleon_include_init_with_doc = True
napoleon_use_admonition_for_notes = False
napoleon_use_param = False
napoleon_use_ivar = False

autosectionlabel_prefix_document = True

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

#html_theme = 'alabaster'
#html_theme = 'sphinxdoc'
html_theme = "sphinx_rtd_theme"
#html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
#html_theme = 'bootstrap'
#html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()

# Alabaster side bar
xhtml_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'searchbox.html',
        # 'donate.html',
    ]
}


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
    'css/fdi.css',
]

html_js_files = [
    'js/custom.js',
]

#html_style = 'css/yourtheme.css'

copybutton_prompt_text = r">>> |\.\.\. |\.\.\.: |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True
copybutton_image_path = 'copy-button-yellow.svg'
copybutton_remove_prompts = True

# Theme options are theme-specific and customize the look and feel of a
# theme further.
xhtml_theme_options = {
    'canonical_url': 'http://mercury.bao.ac.cn:9006/mh/fdi',
    'analytics_id': 'UA-XXXXXXX-1',  # Provided by Google in your dashboard
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': 'white',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
    'display_gitlab': True,
    'gitlab_url': 'http://mercury.bao.ac.cn:9006/mh/fdi',
}

XXhtml_theme_options = {
    'page_width': '1200px',
    'sidebar_width': '300px',
    'show_powered_by': True,
    'sidebar_collapse': True,
}


XXXhtml_theme_options = {
    # Navigation bar title. (Default: ``project`` value)
    'navbar_title': "fdi",

    # Tab name for entire site. (Default: "Site")
    'navbar_site_name': "ags",

    # A list of tuples containing pages or urls to link to.
    # Valid tuples should be in the following forms:
    #    (name, page)                 # a link to a page
    #    (name, "/aa/bb", 1)          # a link to an arbitrary relative url
    #    (name, "http://example.com", True) # arbitrary absolute url
    # Note the "1" or "True" value above as the third argument to indicate
    # an arbitrary url.
    'navbar_links': [
        ("Examples", "examples"),
        ("Link", "http://example.com", True),
    ],

    # Render the next and previous page links in navbar. (Default: true)
    'navbar_sidebarrel': True,

    # Render the current pages TOC in the navbar. (Default: true)
    'navbar_pagenav': True,

    # Tab name for the current pages TOC. (Default: "Page")
    'navbar_pagenav_name': "Page",

    # Global TOC depth for "site" navbar tab. (Default: 1)
    # Switching to -1 shows all levels.
    'globaltoc_depth': 2,

    # Include hidden TOCs in Site navbar?
    #
    # Note: If this is "false", you cannot have mixed ``:hidden:`` and
    # non-hidden ``toctree`` directives in the same page, or else the build
    # will break.
    #
    # Values: "true" (default) or "false"
    'globaltoc_includehidden': "true",

    # HTML navbar class (Default: "navbar") to attach to <div> element.
    # For black navbar, do "navbar navbar-inverse"
    'navbar_class': "navbar navbar-inverse",

    # Fix navigation bar to top of page?
    # Values: "true" (default) or "false"
    'navbar_fixed_top': "true",

    # Location of link to source.
    # Options are "nav" (default), "footer" or anything else to exclude.
    'source_link_position': "nav",
}
xxxhtml_theme_options = {
    # Bootswatch (http://bootswatch.com/) theme.
    #
    # Options are nothing (default) or the name of a valid theme
    # such as "cosmo" or "sandstone".
    #
    # The set of valid themes depend on the version of Bootstrap
    # that's used (the next config option).
    #
    # Currently, the supported themes are:
    # - Bootstrap 2: https://bootswatch.com/2
    # - Bootstrap 3: https://bootswatch.com/3
    'bootswatch_theme': "superhero",

    # Choose Bootstrap version.
    # Values: "3" (default) or "2" (in quotes)
    'bootstrap_version': "3",
}
