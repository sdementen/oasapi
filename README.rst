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

.. |commits-since| image:: https://img.shields.io/github/commits-since/sdementen/oasapi/0.1.17.svg
    :alt: Commits since latest release
    :target: https://github.com/sdementen/oasapi/compare/0.1.17...master



.. end-badges

Python library for Web APIs leveraging OpenAPI/Swagger specification, enabling you to:

 - validate an OAS 2.0 document
 - prune an OAS 2.0 document of its unused elements
 - filter endpoints of an OAS 2.0 document to generate a subset of the API
 - [todo] detect changes between two OAS 2.0 documents (what's new, changed, deprecated, removed)
 - [todo] merge multiple OAS 2.0 documents together
 - [todo] rate/score quality of an OAS 2.0 document (documentation coverage, good practices,...)
 - [todo] transform an OAS 2.0 document (add x-... items, rename paths, rewrite basePath, ...)
 - [todo] add/remove securityDefinitions on an OAS 2.0 document
 

Free software license: BSD 3-Clause License

Quickstart
==========

Install oasapi from PyPI with::

    pip install oasapi

You can also install the in-development version with::

    pip install https://github.com/sdementen/oasapi/archive/master.zip

OAS Document validation
-----------------------

Validate an OAS 2.0 Document (in JSON or YAML format) with::

    python -m oasapi validate samples/swagger_petstore.json

or if you prefer with the oasapi script::

    oasapi validate samples/swagger_petstore.json

or with the ``sdementen/oasapi`` Docker image (available on Docker Hub)::

    docker run sdementen/oasapi validate http://petstore.swagger.io/v2/swagger.json


You can also pipe a swagger to the command (if oasapi cannot retrieve the file by itself)::

    type samples/swagger_petstore.json | oasapi validate -
    type samples/swagger_petstore.json | docker run -i sdementen/oasapi validate -
    curl http://petstore.swagger.io/v2/swagger.json | oasapi validate -
    curl -s http://petstore.swagger.io/v2/swagger.json | docker run -i sdementen/oasapi validate -


OAS Document filtering
----------------------

Similarly, you can use the filter command to filter an OAS 2.0 document and keep only specific operations.
For instance, to keep only operations with the tag 'pet', the security scope at most 'read:pets' and the operations matching
the regepx "(GET|PUT) .*petid.*" (all paths containing 'petid' with verb GET or PUT), run::

    oasapi filter http://petstore.swagger.io/v2/swagger.json -o new_swagger.json --tag pet --security-scope read:pets --path "(GET|PUT) .*petid.*"

(you will see that the new_swagger.json has only one operation left ``GET /pet/{petId}``).

OAS Document pruning
--------------------

Another useful command is pruning, which takes an OAS 2.0 document and prune it of its unused elements as::

    oasapi prune http://petstore.swagger.io/v2/swagger.json -o new_swagger.json


Documentation
=============

https://oasapi.readthedocs.io/

Development
===========

https://oasapi.readthedocs.io/en/latest/contributing.html#development
