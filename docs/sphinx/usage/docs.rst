=======================
Maintain Documentations
=======================

.. contents:: Table of Contents
	      :depth: 3
		      
Sphinx Directory Layout
=======================
		      
FDI uses *Sphinx* to produce, maintain, and format documents, which reside in ```fdi/docs/sphinx```::


  sphinx
  ├── api
  │   ├── api.rst
  │   └── fdi
  │       ├── fdi.dataset.resources.rst
  │       ├── fdi.dataset.rst
  │       ├── fdi.httppool.model.rst
  │       ├── fdi.httppool.route.rst
  │       ├── fdi.httppool.rst
  │       ├── fdi.httppool.schema.rst
  │       ├── fdi.pal.resources.rst
  │       ├── fdi.pal.rst
  │       ├── fdi.pns.resources.rst
  │       ├── fdi.pns.rst
  │       ├── fdi.rst
  │       ├── fdi.utils.rst
  │       └── modules.rst
  ├── conf.py
  ├── index.rst
  ├── Makefile
  ├── tree.txt
  ├── usage
  │   ├── dataset.rst
  │   ├── dockers.rst
  │   ├── httppool.rst
  │   ├── installation.rst
  │   ├── pal.rst
  │   ├── pns.rst
  │   ├── product.rst
  │   └── quickstart.rst
  ├── _static
  │   ├── classes_dataset.png
  │   ├── classes_pal.png
  │   ├── classes_pns.png
  │   ├── copy-button-yellow.svg
  │   ├── copy-button.svg
  │   ├── css
  │   │   ├── copybutton.css
  │   │   ├── custom.css
  │   │   └── fdi.css
  │   ├── css-sv
  │   │   ├── aiohttp.css_t
  │   │   ├── bootstrap.css
  │   │   ├── bootstrap.min.css
  │   │   ├── nature.css
  │   │   ├── _bootswatch.scss
  │   │   └── _variables.scss
  │   ├── ipython_config.py1
  │   ├── packages_dataset.png
  │   ├── packages_pal.png
  │   ├── packages_pns.png
  │   └── product.png
  └── _templates
  ├── about.html
  ├── layout.html
  └── navigation.html


Update Doccuments
=================

Install related Packages
------------------------


.. code-block:: shell

           python3 -m pip install -U -e .[PUB]

Make your changes to take effect
--------------------------------

As the FDI package changes, run in FDI package dir this to update class/package diagrams:

.. code-block:: shell

		make docs_plots

Run

.. code-block:: shell

		make docs_api

to update API documents

Use this

.. code-block:: shell

		make docs_html

after you modifify any `.rst` files above or plots or API infor have been updated. Use your web browser to open the newly generated document: example ``file:///D:/code/fdi/docs/html/index.html``

Translate Documents
===================

TBW

See https://www.sphinx-doc.org/en/master/usage/advanced/intl.html
