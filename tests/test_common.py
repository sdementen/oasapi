import pytest
import yaml

from oasapi.common import find_keys, extract_references, commonprefix

swagger_find_keys = yaml.load(
    """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths:
  /foo:
    parameters: []
    get:
      operationId: this-is-an-operation-id
      parameters:
      - name: param1
        in: body
        schema:
          type: object
          properties:
            operationId:
              example: this-is-not-an-operation-id
            security:
              example: this-is-not-a-security
            parameters:
              example: this-is-not-a-parameters
      responses:
        200:
          description: OK
        300:
          $ref: some-reference
      security: []
security: []
"""
)


def test_find_keys_operation_id():
    results = find_keys(swagger_find_keys, "operationId")

    assert set(results) == {("this-is-an-operation-id", ("paths", "/foo", "get"))}


def test_find_keys_ref():
    results = find_keys(swagger_find_keys, "$ref")

    assert list(results) == [("some-reference", ("paths", "/foo", "get", "responses", 300))]


def test_find_keys_security():
    results = find_keys(swagger_find_keys, "security")

    assert list(results) == [([], ()), ([], ("paths", "/foo", "get"))]


def test_find_keys_parameters():
    results = find_keys(swagger_find_keys, "parameters")

    assert list(results) == [
        ([], ("paths", "/foo")),
        (
            [
                {
                    "in": "body",
                    "name": "param1",
                    "schema": {
                        "properties": {
                            "operationId": {"example": "this-is-not-an-operation-id"},
                            "parameters": {"example": "this-is-not-a-parameters"},
                            "security": {"example": "this-is-not-a-security"},
                        },
                        "type": "object",
                    },
                }
            ],
            ("paths", "/foo", "get"),
        ),
    ]


def test_find_keys_not_supported_key():
    with pytest.raises(AssertionError, match="Key 'paths' not yet handled in 'find_keys'"):
        list(find_keys(swagger_find_keys, "paths"))


swagger_extract_references = yaml.load(
    """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths:
  /foo:
    get:
      parameters:
      - in: "body"
        name: "body"
        schema:
          $ref: "#/definitions/some-definition"
      responses:
        200:
          $ref: "#/responses/some-response"
definitions:
  some-definition:
    type: "object"
    properties:
      prop1:
        $ref: "#/definitions/some-other-definition"
  some-other-definition: {}
  some-orphan-definition:
    type: "object"
    properties:
      prop1:
        $ref: "#/definitions/some-other-orphan-definition"
  some-other-orphan-definition: {}
responses:
  some-response:
    description: OK
"""
)


def test_extract_references():
    result = extract_references(swagger_extract_references)

    assert result == {
        ("definitions", "some-definition", ("paths", "/foo", "get", "parameters", 0, "schema")),
        (
            "definitions",
            "some-other-definition",
            ("definitions", "some-definition", "properties", "prop1"),
        ),
        (
            "definitions",
            "some-other-orphan-definition",
            ("definitions", "some-orphan-definition", "properties", "prop1"),
        ),
        ("responses", "some-response", ("paths", "/foo", "get", "responses", 200)),
    }


def test_commonprefix_empty():
    result = commonprefix([])
    assert result == ""


def test_commonprefix_nocommon():
    swagger = yaml.load(
        """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths:
  /: {}
  /baz: {}
  /v1/path1: {}
  /v1/path2: {}
  /v1/path/path3: {}
  /v1/path/path4: {}
    """
    )

    result = commonprefix(swagger["paths"].keys())
    assert result == ""


def test_commonprefix_1level_common():
    swagger = yaml.load(
        """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths:
  /v1/path1: {}
  /v1/path2: {}
  /v1/path/path3: {}
  /v1/path/path4: {}
    """
    )

    result = commonprefix(swagger["paths"].keys())
    assert result == "/v1"


def test_commonprefix_2levels_common():
    swagger = yaml.load(
        """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths:
  /v1/path/path3: {}
  /v1/path/path4: {}
    """
    )

    result = commonprefix(swagger["paths"].keys())
    assert result == "/v1/path"


def test_commonprefix_single_case():
    swagger = yaml.load(
        """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths:
  /v1/path/path3/: {}
    """
    )

    result = commonprefix(swagger["paths"].keys())
    assert result == "/v1/path/path3"
