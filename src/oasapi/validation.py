"""Swagger 2.0 validation

see https://github.com/swagger-api/swagger-editor/tree/master/src/plugins/validate-semantic
for semantic rules (i.e. beyond teh JSONSchema validation of the swagger)"""
import json
from itertools import groupby
from pathlib import Path
from typing import Set, Dict

from jsonpath_ng import parse, Union
from jsonschema import Draft4Validator

from oasapi.common import get_elements, OPERATIONS_LOWER
from .common import extract_references
from .events import (
    ReferenceNotFoundValidationError,
    ParameterDefinitionValidationError,
    SecurityDefinitionNotFoundValidationError,
    OAuth2ScopeNotFoundInSecurityDefinitionValidationError,
    DuplicateOperationIdValidationError,
    JsonSchemaValidationError,
    ValidationError,
)


def check_security(swagger: Dict):
    """
    Check that uses of security with its scopes matches a securityDefinition

    :param swagger:
    :return:
    """
    events = set()

    secdefs = swagger.get("securityDefinitions", {})

    security_jspath = Union(
        parse("security.[*].*"), parse(f"paths.*.({'|'.join(OPERATIONS_LOWER)}).security.[*].*")
    )

    for sec_key, scopes, path in get_elements(swagger, security_jspath):
        # retrieve security definition name from security declaration
        secdef = secdefs.get(sec_key)

        if secdef is None:
            events.add(
                SecurityDefinitionNotFoundValidationError(
                    path=path, reason=f"securityDefinitions '{sec_key}' does not exist"
                )
            )
        else:
            # retrieve scopes declared in the secdef
            declared_scopes = secdef.get("scopes", [])
            if not isinstance(scopes, list):
                continue
            # verify scopes can be resolved
            for scope in scopes:
                if scope not in declared_scopes:
                    events.add(
                        OAuth2ScopeNotFoundInSecurityDefinitionValidationError(
                            path=path + (scope,),
                            reason=f"scope {scope} is not declared in the scopes of the securityDefinitions '{sec_key}'",
                        )
                    )

    return events


def _check_parameter(param: Dict, path_param):
    events = set()

    default = param.get("default")
    type = param.get("type")
    enum = param.get("enum")

    # check if type==array that there is an items
    if type == "array" and "items" not in param:
        events.add(
            ParameterDefinitionValidationError(
                path=path_param,
                reason=f"The parameter is of type 'array' but is missing an 'items' field",
            )
        )

    # check enum does not contain duplicates
    if enum:
        if len(set(enum)) != len(enum):
            events.add(
                ParameterDefinitionValidationError(
                    path=path_param + ("enum",),
                    reason=f"The enum values {enum} contains duplicate values",
                )
            )
        if default is not None and default not in enum:
            events.add(
                ParameterDefinitionValidationError(
                    path=path_param + ("default",),
                    reason=f"The default value '{default}' is not one of the enum values {enum}",
                )
            )

    # check default value in accordance with type
    if default and type:
        if type == "string" and not isinstance(default, str):
            events.add(
                ParameterDefinitionValidationError(
                    path=path_param + ("default",),
                    reason=f"The default value '{default}' has not the expected type '{type}'",
                )
            )

    return events


def check_parameters(swagger: Dict):
    """
    Check parameters for:
    - duplicate items in enum
    - default parameter is in line with type when type=string

    :param swagger:
    :return:
    """
    events = set()

    security_jspath = Union(
        parse("parameters.[*]"),
        Union(
            parse(f"paths.*.parameters.[*]"),
            parse(f"paths.*.({'|'.join(OPERATIONS_LOWER)}).parameters.[*]"),
        ),
    )

    for _, param, path in get_elements(swagger, security_jspath):
        while True:
            events |= _check_parameter(param, path)
            if param.get("type") == "array":
                # recurse in array items type
                path += ("items",)
                param = param.get("items", {})
            else:
                break

    return events


def check_references(swagger: Dict):
    """
    Find reference in paths, for /definitions/ and /responses/ /securityDefinitions/.

    Follow from these, references to other references, till no more added.

    :param swagger:
    :return:
    """
    reference_types = {"definitions", "responses", "securityDefinitions", "parameters"}

    refs = extract_references(swagger)
    events = set()

    for rt, obj, path in refs:
        assert rt in reference_types, f"Unknown reference type {rt}"
        try:
            swagger[rt][obj]
        except KeyError:
            events.add(
                ReferenceNotFoundValidationError(
                    path=path, reason=f"reference '#/{rt}/{obj}' does not exist"
                )
            )

    return events


def detect_duplicate_operationId(swagger: Dict):
    """Return list of Action with duplicate operationIds"""
    events = set()

    # retrieve all operationIds
    operationId_jspath = parse(f"paths.*.({'|'.join(OPERATIONS_LOWER)}).operationId")

    def get_operationId_name(name_value_path):
        return name_value_path[1]

    operationIds = sorted(get_elements(swagger, operationId_jspath), key=get_operationId_name)

    for opId, key_pths in groupby(operationIds, key=get_operationId_name):
        pths = tuple(subpth for _, _, subpth in key_pths)
        if len(pths) > 1:
            pth_first, *pths = pths
            for pth in pths:
                events.add(
                    DuplicateOperationIdValidationError(
                        path=pth,
                        path_already_used=pth_first,
                        reason=f"the operationId '{opId}' is already used in an endpoint",
                        operationId=opId,
                    )
                )

    return events


def validate_swagger(swagger: Dict) -> Set[ValidationError]:
    """
    Validate a swagger specification.

    The validations checks the following points:

    - validate against re. OAS 2.0 schema
    - no missing reference
    - unicity of operationId
    - no missing securityDefinition
    - consistency of parameters (default value vs type)

    :param swagger: the swagger spec
    :return: a set of errors
    """

    # validate the json schema of the swagger_lib
    schema = json.load((Path(__file__).parent / "schemas" / "schema_swagger.json").open())
    v = Draft4Validator(schema)

    errors = (
        {
            JsonSchemaValidationError(path=tuple(error.absolute_path), reason=error.message)
            for error in v.iter_errors(swagger)
        }
        | check_references(swagger)
        | check_security(swagger)
        | check_parameters(swagger)
        | detect_duplicate_operationId(swagger)
    )

    return errors
