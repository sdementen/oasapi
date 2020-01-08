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

.. |commits-since| image:: https://img.shields.io/github/commits-since/sdementen/oasapi/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/sdementen/oasapi/compare/v0.1.0...master



.. end-badges

Python library for Web APIs leveraging OpenAPI/Swagger specification

* Free software: BSD 3-Clause License

Installation
============

::

    pip install oasapi

You can also install the in-development version with::

    pip install https://github.com/sdementen/oasapi/archive/master.zip


Documentation
=============


https://oasapi.readthedocs.io/


Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
