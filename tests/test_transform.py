import yaml

from oasapi.events import (
    ReferenceNotUsedFilterAction,
    OAuth2ScopeNotUsedAction,
    SecurityDefinitionNotUsedAction,
)
from oasapi.transform import prune_unused_global_items, prune_unused_security_definitions


def test_prune_unused_references():
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
            400:
              $ref: "#/responses/some-response"
    definitions:
      some-definition: {}
    responses:
      some-response:
        $ref: "#/responses/some-other-response"
      some-other-response:
        $ref: "#/responses/some-another-response"
      some-another-response:
        $ref: "#/responses/some-response"
      some-unused-response:
        foo: baz

        """
    swagger = yaml.safe_load(swagger_str)

    swagger, actions = prune_unused_global_items(swagger)

    assert actions == [
        ReferenceNotUsedFilterAction(
            path=("responses", "some-unused-response"),
            reason="reference not used",
            type="Reference filtered out",
        )
    ]
    assert swagger == {
        "definitions": {"some-definition": {}},
        "info": {"title": "my api", "version": "v1.0"},
        "paths": {
            "/foo": {
                "get": {
                    "responses": {
                        200: {"$ref": "#/definitions/some-definition"},
                        400: {"$ref": "#/responses/some-response"},
                    }
                }
            }
        },
        "responses": {
            "some-another-response": {"$ref": "#/responses/some-response"},
            "some-other-response": {"$ref": "#/responses/some-another-response"},
            "some-response": {"$ref": "#/responses/some-other-response"},
        },
        "swagger": "2.0",
    }


def test_prune_unused_security_definitions():
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
      - sec3: [existing-scope]
    PATCH:
      responses:
        200:
          description: OK
      security:
      - sec1: []
    parameters:
      security: [ {sec-not-exist-but-should-not-raise: []} ]
  security: [ {sec-not-exist-but-should-not-raise: []} ]
security: [{sec4:[]}]
securityDefinitions:
  sec1:
    type: basic
  sec2:
    type: basic
  sec4:
    type: basic
  sec-not-used:
    type: basic
  sec3:
    type: oauth2
    flow: implicit
    authorizationUrl: https://some-existing-auth-server.com
    scopes:
      existing-scope: this is an existing scope
      not-used-scope: this is an unused scope
"""
    swagger = yaml.safe_load(swagger_str)

    swagger, actions = prune_unused_security_definitions(swagger)
    assert swagger == {
        "info": {"title": "my api", "version": "v1.0"},
        "paths": {
            "/foo": {
                "PATCH": {"responses": {200: {"description": "OK"}}, "security": [{"sec1": []}]},
                "get": {
                    "responses": {200: {"description": "OK"}},
                    "security": [{"sec1": []}, {"sec3": ["existing-scope"]}],
                },
                "parameters": {"security": [{"sec-not-exist-but-should-not-raise": []}]},
            },
            "security": [{"sec-not-exist-but-should-not-raise": []}],
        },
        "security": [{"sec4": []}],
        "securityDefinitions": {
            "sec1": {"type": "basic"},
            "sec3": {
                "authorizationUrl": "https://some-existing-auth-server.com",
                "flow": "implicit",
                "scopes": {"existing-scope": "this is an " "existing " "scope"},
                "type": "oauth2",
            },
            "sec4": {"type": "basic"},
        },
        "swagger": "2.0",
    }
    assert actions == [
        SecurityDefinitionNotUsedAction(
            path=("securityDefinitions", "sec2"),
            reason="security definition not used",
            type="Security definition removed",
        ),
        SecurityDefinitionNotUsedAction(
            path=("securityDefinitions", "sec-not-used"),
            reason="security definition not used",
            type="Security definition removed",
        ),
        OAuth2ScopeNotUsedAction(
            path=("securityDefinitions", "sec3", "scopes", "not-used-scope"),
            reason="oauth2 scope not used",
            type="Oauth2 scope removed",
        ),
    ]
