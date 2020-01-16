import yaml

from oasapi.common import commonprefix

swagger_find_keys = yaml.safe_load(
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

swagger_extract_references = yaml.safe_load(
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


def test_commonprefix_empty():
    result = commonprefix([])
    assert result == ""


def test_commonprefix_nocommon():
    swagger = yaml.safe_load(
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
    swagger = yaml.safe_load(
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
    swagger = yaml.safe_load(
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
    swagger = yaml.safe_load(
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
