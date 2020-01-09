
Changelog
=========


0.1.7 (2019-01-09)
------------------

* Support URL and stdin (with -) as SWAGGER for the CLI


0.1.6 (2019-01-08)
------------------

* [dev] PyPI deployment through Travis CI


0.1.5 (2019-01-08)
------------------

* Fix script form of the cli (``oasapi`` instead of ``python -m oasapi``)


0.1.4 (2019-01-08)
------------------

* Explicit support only for python >= 3.6 (no py35 as use of f-string)
* [dev] Move local build of docs from dist/docs to docs/dist to avoid cluttering dist


0.1.3 (2019-01-08)
------------------

* [dev] Add git pre-commit hooks for black and flake
* [dev] Do not use isort
* [dev] Fix black + flake8 issues


0.1.2 (2019-01-08)
------------------

* Fix model & reporting of duplicate operationIds
* Add documentation on the CLI Usage

0.1.1 (2019-01-08)
------------------

* Add pyyaml dependencies (to support OAS in yaml format)

0.1.0 (2019-01-08)
------------------

* First release on PyPI.
* Implementation of the validation of an OAS 2.0 (aka swagger) file
