============================
**Data Containers**: Product
============================

.. contents:: Table of Contents
	      :depth: 3

Product
=======

Product is what links all fdi components together.

Data and Meta Data
-------------------

.. image:: ../_static/product.png
   :width: 30%
		   
A product has
   * zero or more datasets: defining well described data entities (say images, tables, spectra etc...). 
   * accompanying meta data -- required information such as

     * the classification of this product,
     * the creator this product,
     * when was the product created?
     * what does the data reflect? (its intended use scope)
     * and so on;
     * possible additional meta data specific to that particular product type.
   * history of this product: how was this data created.
   * References of relevant products that form a context of this product

     
History
-------

The history is a lightweight mechanism to record the origin of this product or changes made to this product. Lightweight means, that the Product data itself does not  records changes, but external parties can attach additional information to the Product which reflects the changes.

The sole purpose of the history interface of a Product is to allow notably pipeline tasks (as defined by the pipeline framework) to record what they have done to generate and/or modify a Product. 

Serializable
---------------

In order to transfer data across the network between heterogeneous nodes data needs to be serializable.
JSON format is used considering to transfer serialized data for its wide adoption, availability of tools, ease to use with Python, and simplicity.


Product Definition Methodology
------------------------------

Data Products almost always are classified in heirachical orders, reflecting the underlying relation of the data model. Many Products are found to have inheritance relations when comparing their metadata and datasets. Therefore an object-oriented approach is chosen to anlize and define the structure, function, and interface of Products here.

First specify built-in Parameters  in in YAML format, which is suitable for reading by both humans and machines. A helper utility ``yaml2python``  to generate test-ready Python code of product class module containing the built-ins.

The YAML schema allows a child Product to inherit metadata definition from one or multiple parent Products. Overriding is also allowed.

BaseProduct
"""""""""""

This is the definition file `BaseProduct.yml`

.. include:: ../../../fdi/dataset/resources/BaseProduct.yml
   :code: yaml

The preamble key-value pairs give information about this definition:

:name:  of this product
:description: -- Information about this product
:parents: -- Children products Inherit parent’s metadata
:level: Applicable Level
:schema: version of format of this YAML document

From the creation process requires every product to carry the following metadata entries about itself, 

:description: (Also in native language if it is not English.)
:type: -- In software or business domain
:version: -- Products of the same format must be versioned, configuration controlled, and be ready to deal with version differences between inputs , algorithms, software and pipelines.
:FORMATV: -- Version of this document with Schema information, e.g. 1.4.1.2
:creator, rootCause, creationDate: -- Who, why, when, where

The parameters are tabulated below.

.. include:: ../../../fdi/dataset/resources/BaseProduct.txt
   :code: text

Examples (from :doc:`quickstart` page):

.. include:: quickstart.rst
   :start-after: Product with metadata and datasets
   :end-before: pal - Product Access Layer

