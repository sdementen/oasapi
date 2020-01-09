import yaml

from oasapi.events import (
    JsonSchemaValidationError,
    ReferenceNotFoundValidationError,
    DuplicateOperationIdValidationError,
    ParameterDefinitionValidationError,
    SecurityDefinitionNotFoundValidationError,
    OAuth2ScopeNotFoundInSecurityDefinitionValidationError,
)
from oasapi.validation import (
    validate_swagger,
    check_references,
    detect_duplicate_operationId,
    check_parameters,
    check_security,
)


def test_minimal_compliant_swagger():
    """This is the minimal testing"""
    swagger_str = """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths: {}
"""
    swagger = yaml.load(swagger_str)
    results = validate_swagger(swagger)

    # no error in this basic test
    assert results == set()


def test_empty_swagger():
    """This is the minimal testing"""
    results = validate_swagger({})

    # no error in this basic test
    assert results == {
        JsonSchemaValidationError(
            path=(), reason="'info' is a required property", type="Json schema validator error"
        ),
        JsonSchemaValidationError(
            path=(), reason="'paths' is a required property", type="Json schema validator error"
        ),
        JsonSchemaValidationError(
            path=(), reason="'swagger' is a required property", type="Json schema validator error"
        ),
    }


def test_schema_error():
    swagger_str = """
swagger: '2.0'
info:
  version: 1.0
  title: my api
paths: {}
"""
    swagger = yaml.load(swagger_str)
    results = validate_swagger(swagger)

    # no error in this basic test
    assert results == {
        JsonSchemaValidationError(
            path=("info", "version"),
            reason="1.0 is not of type 'string'",
            type="Json schema validator error",
        )
    }


def test_check_references():
    swagger_str = """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths:
  /foo:
    get:
      responses:
        200:
          $ref: "#/definitions/some-definition"
        300:
          $ref: "#/definitions/some-not-existing-definition"
        400:
          $ref: "#/responses/some-response"
definitions:
  some-definition: {}
responses:
  some-response:
    description: OK

    """
    swagger = yaml.load(swagger_str)

    results = check_references(swagger)
    assert results == {
        ReferenceNotFoundValidationError(
            path=("paths", "/foo", "get", "responses", 300),
            reason="reference '#/definitions/some-not-existing-definition' does not exist",
            type="Reference not found",
        )
    }


def test_detect_duplicate_operationId():
    swagger_str = """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths:
  /foo:
    get:
      operationId: this-is-a-unique-id
      responses:
        200:
          description: OK
    post:
      operationId: this-is-not-a-unique-id
      responses:
        200:
          description: OK
    put:
      operationId: this-is-not-a-unique-id
      responses:
        200:
          description: OK
    """
    swagger = yaml.load(swagger_str)

    results = detect_duplicate_operationId(swagger)
    assert results == {
        DuplicateOperationIdValidationError(
            path=("paths", "/foo", "put"),
            reason="the operationId 'this-is-not-a-unique-id' is already used in an endpoint",
            operationId="this-is-not-a-unique-id",
            path_first_used=("paths", "/foo", "post"),
            type="Duplicate operationId",
        )
    }


def test_check_parameters():
    swagger_str = """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths:
  /foo:
    parameters:
    - name: param_int
      in: query
      type: integer
      default: 1
    - name: param_str
      in: query
      type: string
      default: [hello, world]
    - name: param_str
      in: query
      type: string
      default: 1
    - name: param_enum_wrong_default
      in: query
      type: string
      enum: [there, are, valid, values]
      default: this-is-not-valid
    - name: param_enum
      in: query
      type: string
      enum: [there, are, valid, values]
      default: there
    - name: param_enum_duplicates
      in: query
      type: string
      enum: [there, are, duplicates, duplicates]
"""
    swagger = yaml.load(swagger_str)

    results = check_parameters(swagger)
    assert results == {
        ParameterDefinitionValidationError(
            path=("paths", "/foo", "parameters", '[1] (param["name"])', "default"),
            reason="The default value '['hello', 'world']' has not the expected type 'string'",
            type="Parameter definition error",
        ),
        ParameterDefinitionValidationError(
            path=("paths", "/foo", "parameters", '[2] (param["name"])', "default"),
            reason="The default value '1' has not the expected type 'string'",
            type="Parameter definition error",
        ),
        ParameterDefinitionValidationError(
            path=("paths", "/foo", "parameters", '[3] (param["name"])', "default"),
            reason="The default value 'this-is-not-valid' is not one of the enum values ['there', 'are', 'valid', 'values']",
            type="Parameter definition error",
        ),
        ParameterDefinitionValidationError(
            path=("paths", "/foo", "parameters", '[5] (param["name"])', "enum"),
            reason="The enum values ['there', 'are', 'duplicates', 'duplicates'] contains duplicate values",
            type="Parameter definition error",
        ),
    }


def test_check_security():
    swagger_str = """
swagger: '2.0'
info:
  version: v1.0
  title: my api
paths:
  /foo:
    get:
      responses:
        200:
          description: OK
      security:
      - sec1: []
        sec2: [not-existing-scope]
      - sec3: [existing-scope]
      - sec-not-exist: []
security: []
securityDefinitions:
  sec1:
    type: basic
  sec2:
    type: basic
  sec3:
    type: oauth2
    flow: implicit
    authorizationUrl: https://some-existing-auth-server.com
    scopes:
      existing-scope: this is an existing scope
"""
    swagger = yaml.load(swagger_str)

    results = check_security(swagger)
    assert results == {
        OAuth2ScopeNotFoundInSecurityDefinitionValidationError(
            path=("paths", "/foo", "get", "security", "sec2", "not-existing-scope"),
            reason="scope not-existing-scope is not declared in the scopes of the securityDefinitions 'sec2'",
            type="Security scope not found",
        ),
        SecurityDefinitionNotFoundValidationError(
            path=("paths", "/foo", "get", "security", "sec-not-exist"),
            reason="securityDefinitions 'sec-not-exist' does not exist",
            type="Security definition not found",
        ),
    }
