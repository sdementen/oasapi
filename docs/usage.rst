==================
Usage with the CLI
==================

Introduction
------------

oasapi offers a command line interface (CLI) to run core operations:

.. command-output:: python -m oasapi

All these operation are also available programmatically through the :ref:`oasapi-package` package.

Alternatively to the syntax herebove, you can call oasapi through the oasapi script:

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


Pipelining commands
-------------------

When using oasapi in pipes, the ``-`` denotes the stdin/stdout.

To pipe a swagger in a command, you replace the path/URL of the swagger with a ``-``:

.. command-output:: curl -s http://petstore.swagger.io/v2/swagger.json | oasapi validate -
   :shell:

To send the output swagger of a command to stdout, you replace the path for the ``--output`` argument with a ``-``
(when using stdout, the format is always YAML).

If you want to silence the commands (ie not sending their message to stderr), you can add the silent argument (``-s``)

For instance, the following command will:

1. get a swagger with curl
2. filter it to keep only the operations with the tag 'pet'
3. prune it of any unused elements
4. validate it and send it to stdout

.. command-output:: curl -s http://petstore.swagger.io/v2/swagger.json | oasapi filter -s --tag pet - --output - | oasapi prune -s - --output - | oasapi validate -s - -o -
   :shell:
   :ellipsis: 10





Validating an OAS 2.0 Document
------------------------------

Validating is an operation that will check the swagger for errors:

 - structural errors, i.e. errors coming from the swagger not complying with the swagger JSON schema
 - semantic errors, i.e. errors beyond the structural ones (e.g. duplicate operationIds)


You can validate a document with the ``validate`` command:

.. command-output:: oasapi validate --help
.. command-output:: oasapi validate samples/swagger_petstore.json
.. command-output:: oasapi validate samples/swagger_petstore_with_errors.json
   :returncode: 1


Filtering an OAS 2.0 Document
-----------------------------

Filtering is an operation that will keep from the swagger only the operations that do match criteria:

 - tags: the operation should have at least one tag from a given list of tags (e.g. ["pet", "store"])
 - operations: the VERB + PATH should match a regexp from a list (e.g. ["POST /pet", "(GET|PUT) /pet/{petId}"])
 - security scopes: the operation should be accessible only with the scopes in a given list of scopes (e.g. ["read:pets"])

You can filter a document with the ``filter`` command:

.. command-output:: oasapi filter --help
.. command-output:: oasapi filter samples/swagger_petstore.json -t pet -t store -sc read:pets -p "POST /pet" -p "(GET|PUT) /pet/{petId}" -o swagger_filtered.yaml

As the ``filter`` command may remove operations, it is a good idea to follow it with a ``prune`` command to remove any elements of the swagger
that would not be used anymore.

For instance, the following command filter the swagger to keep only operations with the tag 'weird' and prune the resulting swagger
afterwards. As no operation has the tag 'weird', the filtering leads to a swagger with no more paths and the pruning will clean the swagger showing
at the end an almost empty swagger.

.. command-output:: oasapi filter samples/swagger_petstore.json -t weird -o - 2> filter_messages | oasapi prune - -o - 2> prune_messages
   :shell:

The operation must match all the three different filter criteria (tags, security scopes and operations regexp) when given.
If you want to apply more advanced filter (like "(tag='pet' AND security-scope='read:pets') or (tag='store')"), you can call the filter
method directly from python and pass these filters (see :py:meth:`oasapi.filter`).

Pruning an OAS 2.0 Document
---------------------------

Pruning is an operation that will 'clean' the swagger by removing any unused elements:

 - global definitions not referenced
 - global parameters not referenced
 - global responses not referenced
 - securityDefinitions not used
 - securityDefinitions oauth2 scopes not used
 - tags not used
 - empty paths (endpoints with no verbs attached)

You can prune a document with the ``prune`` command:

.. command-output:: oasapi prune --help
.. command-output:: oasapi prune samples/swagger_petstore.json
.. command-output:: oasapi prune samples/swagger_petstore_unused_elements.json
   :returncode: 1

