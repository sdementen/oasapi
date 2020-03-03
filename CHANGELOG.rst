
Changelog
=========


0.1.17   (2020-03-03)
---------------------

* fix integer response code raising exception (closes #14)

0.1.16   (2020-02-08)
---------------------

* add documentation of filter in prune + cleanup doc

0.1.15   (2020-02-08)
---------------------

* add filtering of swagger
* support outputting swagger in yaml format
* support silencing the CLI
* [dev] refactor CLI

0.1.13 (2020-01-25)
-------------------

* add validation of parameters required/default
* add validation of parameters default value wrt type/format


0.1.12 (2020-01-17)
-------------------

* add pruning of unused items (definitions, responses, parameters, securityDefinitions/scopes, tags)
* rename validate_swagger function to validate, add prune function

0.1.11 (2020-01-16)
-------------------

* [dev] use jsonpath_ng to walk the swagger
* add timing of validation in CLI if verbose

0.1.10 (2020-01-10)
-------------------

* [dev] fix tag name to remove "v" (for readthedocs latest build)
* [dev] fix travis ci python version for doc

0.1.9 (2020-01-10)
------------------

* Improve validation of array parameters
* Improve documentation

0.1.8 (2020-01-09)
------------------

* Push the sdementen/oasapi docker image to Docker Hub on each release
* Update doc on Docker image use and pipeing a swagger to oasapi

0.1.7 (2020-01-09)
------------------

* Support URL and stdin (with -) as SWAGGER for the CLI


0.1.6 (2020-01-08)
------------------

* [dev] PyPI deployment through Travis CI


0.1.5 (2020-01-08)
------------------

* Fix script form of the cli (``oasapi`` instead of ``python -m oasapi``)


0.1.4 (2020-01-08)
------------------

* Explicit support only for python >= 3.6 (no py35 as use of f-string)
* [dev] Move local build of docs from dist/docs to docs/dist to avoid cluttering dist


0.1.3 (2020-01-08)
------------------

* [dev] Add git pre-commit hooks for black and flake
* [dev] Do not use isort
* [dev] Fix black + flake8 issues


0.1.2 (2020-01-08)
------------------

* Fix model & reporting of duplicate operationIds
* Add documentation on the CLI Usage

0.1.1 (2020-01-08)
------------------

* Add pyyaml dependencies (to support OAS in yaml format)

0.1.0 (2020-01-08)
------------------

* First release on PyPI.
* Implementation of the validation of an OAS 2.0 (aka swagger) file
