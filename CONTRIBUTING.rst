============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Bug reports
===========

When `reporting a bug <https://github.com/sdementen/oasapi/issues>`_ please include:

    * Your operating system name and version.
    * Any details about your local setup that might be helpful in troubleshooting.
    * Detailed steps to reproduce the bug.

Documentation improvements
==========================

The Open API Specifications Advanced Python Introspection library could always use more documentation, whether as part of the
official The Open API Specifications Advanced Python Introspection library docs, in docstrings, or even on the web in blog posts,
articles, and such.

Feature requests and feedback
=============================

The best way to send feedback is to file an issue at https://github.com/sdementen/oasapi/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that code contributions are welcome :)

Development
===========

To set up `oasapi` for local development:

1. Fork `oasapi <https://github.com/sdementen/oasapi>`_
   (look for the "Fork" button).
2. Clone your fork locally::

    git clone git@github.com:sdementen/oasapi.git

3. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

4. When you're done making changes run all the checks and docs builder with `tox <https://tox.readthedocs.io/en/latest/install.html>`_ one command::

    tox

5. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature

6. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just make the pull request.

For merging, you should:

1. Include passing tests (run ``tox``) [1]_.
2. Update documentation when there's new API, functionality etc.
3. Add a note to ``CHANGELOG.rst`` about the changes.
4. Add yourself to ``AUTHORS.rst``.

.. [1] If you don't have all the necessary python versions available locally you can rely on Travis - it will
       `run the tests <https://travis-ci.org/sdementen/oasapi/pull_requests>`_ for each change you add in the pull request.

       It will be slower though ...

Tips
----

To install a minimal virtual environment with tox (see https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments ) ::

    cd path-to-your-oasapi-folder
    python -m venv .env
    ' activate your .env virtualenv
    python -m pip install -r requirements-dev.txt


To install the git pre-commit scripts::

    pre-commit install

To run the tests locally::

    cd path-to-your-oasapi-folder
    ' activate your .env virtualenv
    tox

To build the documentation locally (available in the folder ``docs/dist``, entry point ``docs/dist/index.html``)::

    cd path-to-your-oasapi-folder
    ' activate your .env virtualenv
    tox -e docs

To recreate the tox environments (e.g. if you add a dependency in the setup.py)::

    tox --recreate
    tox --recreate -e py36              '(only the py36 environment)



To run a subset of tests::

    tox -e envname -- pytest -k test_myfeature

To run all the test environments in *parallel* (you need to ``pip install detox``)::

    detox


Tips with PyCharm
-----------------

To run tox within PyCharm, right click on ``tox.ini`` and choose ``Run`` (see https://www.jetbrains.com/help/pycharm/tox-support.html)

Tips to deploy (for the maintainers)
------------------------------------

To bump the version::

    ' update/commit first all your changes including the changelog
    bump2version patch --tag --commit

To build the source distribution::

    ' clean first the /dist folder
    python setup.py sdist


To upload on PyPI Test::

    python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

To upload on PyPI::

    python -m twine upload dist/*

For the setup of the deploy to PyPI step on Travis, the information on https://docs.travis-ci.com/user/deployment/pypi/
(with the online encrypt tool on https://travis-encrypt.github.io/) were useful.
