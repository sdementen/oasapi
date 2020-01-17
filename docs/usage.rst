==================
Usage with the CLI
==================

Introduction
------------

oasapi offers a command line interface (CLI) to run core operations:

.. command-output:: python -m oasapi

All these operation are also available programmatically through the :ref:`oasapi-package` package.

Alternatively to the syntax hereabove, you can call oasapi through the oasapi script:

.. command-output:: oasapi

And there is also a docker image ``sdementen/oasapi`` offering the same script through ``docker run sdementen/oasapi``

Help is available with the ``--help`` option:

.. command-output:: oasapi --help

.. command-output:: oasapi validate --help


Specifying an OAS 2.0 (aka swagger) file
----------------------------------------

The `oasapi` commands will often require an OAS 2.0 Document (aka swagger).
The swagger can be given in JSON or YAML format and can be a local file or a URL.

Example of usage (YAML file)

.. command-output:: oasapi validate samples/swagger_petstore.yaml

Example of usage (JSON file):

.. command-output:: oasapi validate samples/swagger_petstore.json

Example of usage (JSON URL)

.. command-output:: oasapi validate http://petstore.swagger.io/v2/swagger.json

Validating an OAS 2.0 Document
------------------------------

Validating is an operation that will check the swagger for errors::

 - structural errors, i.e. errors coming from the swagger not complying with the swagger JSON schema
 - semantic errors, i.e. errors beyond the structural ones (e.g. duplicate operationIds)


You can validate a document with the ``validate`` command:

.. command-output:: oasapi validate samples/swagger_petstore.json
.. command-output:: oasapi validate samples/swagger_petstore_with_errors.json
   :returncode: 1


Pruning an OAS 2.0 Document
---------------------------

Pruning is an operation that will 'clean' the swagger by removing any unused elements::

 - global definitions not referenced
 - global parameters not referenced
 - global responses not referenced
 - securityDefinitions not used
 - securityDefinitions oauth2 scopes not used
 - tags not used

You can prune a document with the ``prune`` command:

.. command-output:: oasapi prune samples/swagger_petstore.json
.. command-output:: oasapi prune samples/swagger_petstore_unused_elements.json
   :returncode: 1
