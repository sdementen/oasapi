import copy

import pytest
import yaml

from oasapi.compare import compare
from oasapi.events import (
    AddedOperationDiffAction,
    RemovedNotDeprecatedOperationDiffAction,
    RemovedDeprecatedOperationDiffAction,
)


swagger_str = """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths:
  /foo:
    get: {}
    post:
      deprecated: true
    patch: {}
  /foo/baz:
    get: {}
    put: {}
"""


@pytest.fixture(scope="function")
def swagger():
    return yaml.safe_load(swagger_str)


def test_compare(swagger):
    swagger_from = swagger
    swagger_to = copy.deepcopy(swagger)
    paths = swagger_to["paths"]

    # modify the swagger
    paths["/baz"] = dict(get={})
    del paths["/foo/baz"]
    del paths["/foo"]["post"]

    swagger, actions = compare(swagger=swagger_from, swagger_new=swagger_to)

    assert actions == [
        AddedOperationDiffAction(
            path=("paths", "/baz", "get"),
            reason="The operation has been added",
            type="Operation added",
        ),
        RemovedDeprecatedOperationDiffAction(
            path=("paths", "/foo", "post"),
            reason="The operation was deprecated and has been removed",
            type="Deprecated operation removed",
        ),
        RemovedNotDeprecatedOperationDiffAction(
            path=("paths", "/foo/baz", "get"),
            reason="The operation was not yet deprecated but has been removed",
            type="Not deprecated operation removed",
        ),
        RemovedNotDeprecatedOperationDiffAction(
            path=("paths", "/foo/baz", "put"),
            reason="The operation was not yet deprecated but has been removed",
            type="Not deprecated operation removed",
        ),
    ]
