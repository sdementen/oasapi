import copy

import pytest
import yaml

from oasapi.filter import filter, FilterCondition, resolve_security, generate_filter_conditions

swagger_str = """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths:
  /foo:
    get:
      tags: [tag1, tag2, tag3]
      security:
      - sec1: [read]
        sec2: [write]
    post:
      tags: [tag1]
      security: []
    patch:
      tags: [tag2]
      security:
      - sec2: [write]
  /foo/baz:
    get:
      tags: [tag3]
      security:
      - sec1: [read]
        sec2: [read]
    post:
      tags: [tag1, tag2]
    patch:
      tags: [tag2, tag3]
security:
- sec1: [read]
- sec2: [write]
"""


@pytest.fixture(scope="function")
def swagger():
    return yaml.safe_load(swagger_str)


def test_resolve_security(swagger):
    # add an endpoint without security
    swagger["paths"]["/no-security"] = dict(get={})
    # remember security of endpoint /foo/baz.get
    before = copy.deepcopy(swagger["paths"]["/foo/baz"]["get"]["security"])

    # resolve security
    resolve_security(swagger)

    # check security has changed on the /no-security.get operation but no on the other
    assert swagger["paths"]["/no-security"]["get"]["security"] == swagger["security"]
    assert swagger["paths"]["/foo/baz"]["get"]["security"] == before


def test_generate_filter_conditions_simple():
    filter = generate_filter_conditions([FilterCondition(tags=["tag1"])])

    assert not filter((), {})
    assert not filter((), dict(tags=["tag2"]))

    assert filter((), dict(tags=["tag1"])) == dict(tags=["tag1"])
    assert filter((), dict(tags=["tag2", "tag1"])) == dict(tags=["tag1"])


def test_generate_filter_conditions_two_no_merge():
    filter = generate_filter_conditions(
        [FilterCondition(tags=["tag1"]), FilterCondition(tags=["tag2"])]
    )
    assert not filter((), {})
    assert not filter((), dict(tags=["tag3"]))

    assert filter((), dict(tags=["tag1"])) == dict(tags=["tag1"])
    assert filter((), dict(tags=["tag2", "tag1"])) == dict(tags=["tag1"])
    assert filter((), dict(tags=["tag2"])) == dict(tags=["tag2"])


def test_generate_filter_conditions_two_with_merge():
    filter = generate_filter_conditions(
        [FilterCondition(tags=["tag1"]), FilterCondition(tags=["tag2"])], merge_matches=True
    )
    assert not filter((), {})
    assert not filter((), dict(tags=["tag3"]))

    assert filter((), dict(tags=["tag1"])) == dict(tags=["tag1"])
    assert filter((), dict(tags=["tag2", "tag1"])) == dict(tags=["tag1", "tag2"])
    assert filter((), dict(tags=["tag2"])) == dict(tags=["tag2"])


def test_generate_filter_conditions_operation():
    filter = generate_filter_conditions(
        [FilterCondition(operations=["get /foo"]), FilterCondition(operations=["patch /foo/baz"])],
        merge_matches=True,
    )
    assert filter(("paths", "/foo", "get"), {}) == {}
    assert filter(("paths", "/foo/baz", "patch"), {}) == {}
    assert filter(("paths", "/foo/Baz", "PaTCH"), {}) == {}

    assert not filter(("paths", "/baz", "get"), {})
    assert not filter(("paths", "/foo", "put"), {})


def test_generate_filter_conditions_security():
    filter = generate_filter_conditions([FilterCondition(security_scopes=["sec1"])])
    assert not filter((), {})
    assert not filter((), dict(tags=["tag2"]))
    assert not filter((), dict(security=[{"oauth": ["tag1"]}]))

    assert filter((), dict(security=[{"oauth": ["sec1"]}])) == {"security": [{"oauth": ["sec1"]}]}
    assert filter((), dict(security=[{"oauth": ["sec1", "sec2"]}])) == {
        "security": [{"oauth": ["sec1"]}]
    }


conditions = [
    (
        [FilterCondition(tags=["tag2"]), FilterCondition(tags=["tag1"])],
        {
            "info": {"title": "my api", "version": "v1.0"},
            "paths": {
                "/foo": {
                    "get": {
                        "security": [{"sec1": ["read"], "sec2": ["write"]}],
                        "tags": ["tag2", "tag1"],
                    },
                    "patch": {"security": [{"sec2": ["write"]}], "tags": ["tag2"]},
                    "post": {"security": [], "tags": ["tag1"]},
                },
                "/foo/baz": {"patch": {"tags": ["tag2"]}, "post": {"tags": ["tag2", "tag1"]}},
            },
            "security": [{"sec1": ["read"]}, {"sec2": ["write"]}],
            "swagger": "2.0",
        },
    ),
    (
        [FilterCondition(tags=["tag2"])],
        {
            "info": {"title": "my api", "version": "v1.0"},
            "paths": {
                "/foo": {
                    "get": {"security": [{"sec1": ["read"], "sec2": ["write"]}], "tags": ["tag2"]},
                    "patch": {"security": [{"sec2": ["write"]}], "tags": ["tag2"]},
                },
                "/foo/baz": {"patch": {"tags": ["tag2"]}, "post": {"tags": ["tag2"]}},
            },
            "security": [{"sec1": ["read"]}, {"sec2": ["write"]}],
            "swagger": "2.0",
        },
    ),
    (
        [FilterCondition(tags=["tag2"], security_scopes=["read"])],
        {
            "info": {"title": "my api", "version": "v1.0"},
            "paths": {
                "/foo": {"get": {"security": [{"sec1": ["read"]}], "tags": ["tag2"]}},
                "/foo/baz": {
                    "patch": {"security": [{"sec1": ["read"]}], "tags": ["tag2"]},
                    "post": {"security": [{"sec1": ["read"]}], "tags": ["tag2"]},
                },
            },
            "security": [{"sec1": ["read"]}],
            "swagger": "2.0",
        },
    ),
    (
        [FilterCondition(security_scopes=["write"]), FilterCondition(security_scopes=["read"])],
        {
            "info": {"title": "my api", "version": "v1.0"},
            "paths": {
                "/foo": {
                    "get": {
                        "security": [{"sec2": ["write"]}, {"sec1": ["read"]}],
                        "tags": ["tag1", "tag2", "tag3"],
                    },
                    "patch": {"security": [{"sec2": ["write"]}], "tags": ["tag2"]},
                },
                "/foo/baz": {
                    "get": {"security": [{"sec1": ["read"], "sec2": ["read"]}], "tags": ["tag3"]},
                    "patch": {
                        "security": [{"sec2": ["write"]}, {"sec1": ["read"]}],
                        "tags": ["tag2", "tag3"],
                    },
                    "post": {
                        "security": [{"sec2": ["write"]}, {"sec1": ["read"]}],
                        "tags": ["tag1", "tag2"],
                    },
                },
            },
            "security": [{"sec2": ["write"]}, {"sec1": ["read"]}],
            "swagger": "2.0",
        },
    ),
]


@pytest.mark.parametrize("conditions,expected", conditions)
def test_filtering_conditions(swagger, conditions, expected):
    swagger_filtered, actions = filter(swagger, mode="keep_only", conditions=conditions)

    assert swagger_filtered == expected

    # no error in this basic test
    assert actions == []


@pytest.mark.parametrize("global_security", [True, False])
def test_filtering_conditions_no_global_security(swagger, global_security):
    if not global_security:
        del swagger["security"]

    swagger_filtered, actions = filter(
        swagger,
        mode="keep_only",
        conditions=[FilterCondition(security_scopes=["inexisting-scope"])],
    )

    assert swagger_filtered == {
        "info": {"title": "my api", "version": "v1.0"},
        "paths": {"/foo": {}, "/foo/baz": {}},
        "swagger": "2.0",
    }

    # no error in this basic test
    assert actions == []
