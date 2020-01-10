=====
Usage
=====

Command line interface
----------------------

oasapi offers a CLI to run core commands:

.. command-output:: python -m oasapi

Alternatively to the syntax hereabove, you can call oasapi through the oasapi script:

.. command-output:: oasapi

And there is also a docker image ``sdementen/oasapi`` offering the same script through ``docker run sdementen/oasapi``

Validating an OAS 2.0 (aka swagger) file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `validate` command will validate a file given as parameter

.. command-output:: python -m oasapi validate --help

Example of usage (YAML file)

.. command-output:: python -m oasapi validate samples/swagger_petstore.yaml

Example of usage (JSON file):

.. command-output:: python -m oasapi validate samples/swagger_petstore.json
.. command-output:: python -m oasapi validate samples/swagger_petstore_with_errors.json

Example of usage (JSON URL)

.. command-output:: python -m oasapi validate http://petstore.swagger.io/v2/swagger.json

