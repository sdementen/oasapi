========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |requires|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/oasapi/badge/?style=flat
    :target: https://readthedocs.org/projects/oasapi
    :alt: Documentation Status

.. |travis| image:: https://api.travis-ci.org/sdementen/oasapi.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/sdementen/oasapi

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/sdementen/oasapi?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/sdementen/oasapi

.. |requires| image:: https://requires.io/github/sdementen/oasapi/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/sdementen/oasapi/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/sdementen/oasapi/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/sdementen/oasapi

.. |version| image:: https://img.shields.io/pypi/v/oasapi.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/oasapi

.. |wheel| image:: https://img.shields.io/pypi/wheel/oasapi.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/oasapi

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/oasapi.svg
    :alt: Supported versions
    :target: https://pypi.org/project/oasapi

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/oasapi.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/oasapi

.. |commits-since| image:: https://img.shields.io/github/commits-since/sdementen/oasapi/v0.1.7.svg
    :alt: Commits since latest release
    :target: https://github.com/sdementen/oasapi/compare/v0.1.7...master



.. end-badges

Python library for Web APIs leveraging OpenAPI/Swagger specification, enabling:

 - validation of an OAS 2.0 document
 - [todo] control backward compability between two OAS 2.0 documents
 - [todo] rewriting the basePath and paths of an OAS 2.0 document
 - [todo] filtering endpoints of an OAS 2.0 document to generate a subset of the API
 - [todo] adding/removing securityDefinitions on an OAS 2.0 document

Free software license: BSD 3-Clause License

Quickstart
==========

Install oasapi from PyPI with::

    pip install oasapi

You can also install the in-development version with::

    pip install https://github.com/sdementen/oasapi/archive/master.zip


Validate an OAS 2.0 Document (in JSON or YAML format) with:

.. command-output:: python -m oasapi validate samples/swagger_petstore.json

or if you prefer with:

.. command-output:: oasapi validate samples/swagger_petstore.json

If you want to use docker, the `sdementen/oasapi` image is available on Docker Hub:

.. command-output:: docker run sdementen/oasapi validate http://petstore.swagger.io/v2/swagger.json

If you have issues retrieving a swagger over http/https via oasapi (issues with proxy, certificate, ...), you
can pipe the content to oasapi:

.. command-output:: curl -s http://petstore.swagger.io/v2/swagger.json | oasapi validate -
   :shell:
.. command-output:: curl -s http://petstore.swagger.io/v2/swagger.json | docker run -i sdementen/oasapi validate -
   :shell:

Documentation
=============

https://oasapi.readthedocs.io/

Development
===========

https://oasapi.readthedocs.io/en/latest/contributing.html#development
