=====
Usage
=====

Command line interface
----------------------

oasapi offers a CLI to run core commands

.. command-output:: python -m oasapi

Validating an OAS 2.0 (aka swagger) file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `validate` command will validate a file given as paramter

.. command-output:: python -m oasapi validate --help

Example of usage

.. command-output:: python -m oasapi validate samples/swagger_petstore.json
.. command-output:: python -m oasapi validate samples/swagger_petstore_with_errors.json
