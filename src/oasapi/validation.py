"""Swagger 2.0 validation

see https://github.com/swagger-api/swagger-editor/tree/master/src/plugins/validate-semantic
for semantic rules (i.e. beyond teh JSONSchema validation of the swagger)"""
import json
from itertools import groupby
from pathlib import Path
from typing import Set

from jsonschema import Draft4Validator

from .common import extract_references, find_keys
from .events import (
    ReferenceNotFoundValidationError,
    ParameterDefinitionValidationError,
    SecurityDefinitionNotFoundValidationError,
    OAuth2ScopeNotFoundInSecurityDefinitionValidationError,
    DuplicateOperationIdValidationError,
    JsonSchemaValidationError,
    ValidationError,
)


def check_security(swagger):
    """
    Check that uses of security with its scopes matches a securityDefinition

    :param swagger:
    :return:
    """
    events = set()

    secdefs = swagger.get("securityDefinitions", {})

    for secs, path in find_keys(swagger, "security"):
        for sec in secs:
            # retrieve security definition name from security declaration
            for sec_key in sec.keys():
                secdef = secdefs.get(sec_key)
                if secdef is None:
                    events.add(
                        SecurityDefinitionNotFoundValidationError(
                            path=path + ("security", sec_key),
                            reason=f"securityDefinitions '{sec_key}' does not exist",
                        )
                    )
                else:
                    # retrieve scopes declared in the secdef
                    scopes = secdef.get("scopes", [])
                    # verify scopes can be resolved
                    for scope in sec[sec_key]:
                        if scope not in scopes:
                            events.add(
                                OAuth2ScopeNotFoundInSecurityDefinitionValidationError(
                                    path=path + ("security", sec_key, scope),
                                    reason=f"scope {scope} is not declared in the scopes of the securityDefinitions '{sec_key}'",
                                )
                            )

    return events


def check_parameters(swagger):
    """
    Check parameters for:
    - duplicate items in enum
    - default parameter is in line with type when type=string

    :param swagger:
    :return:
    """
    events = set()

    for parameters, path in find_keys(swagger, "parameters"):
        for iparam, param in enumerate(parameters):
            default = param.get("default")
            type = param.get("type")
            enum = param.get("enum")
            path_param = path + ("parameters", f'[{iparam}] (param["name"])')
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


def check_references(swagger):
    """
    Find reference in paths, for /definitions/ and /responses/ /securityDefinitions/.

    Follow from these, references to other references, till no more added
    :param swagger:
    :return:
    """
    reference_types = {"definitions", "responses", "securityDefinitions"}

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


def detect_duplicate_operationId(swagger):
    """Return list of Action with duplicate operationIds"""
    # retrieve all operationIds
    opIds = list(find_keys(swagger["paths"], "operationId", path=("paths",)))

    events = set()

    for opId, key_pths in groupby(sorted(opIds), key=lambda key_pth: key_pth[0]):
        pths = tuple(subpth for _, subpth in key_pths)

        if len(pths) > 1:
            pth_first, *pths = pths
            for pth in pths:
                events.add(
                    DuplicateOperationIdValidationError(
                        path=pth,
                        path_first_used=pth_first,
                        reason=f"the operationId '{opId}' is already used in an endpoint",
                        operationId=opId,
                    )
                )

    return events


def validate_swagger(swagger) -> Set[ValidationError]:
    """
    Validate a swagger specification.

    The validations checks the following points
    - valide swagger re. OAS 2.0 schema
    - no missing reference
    - unicity of operationId
    It also proposes suggestions for:
    - health endpoint
    - request_id header
    - okta securisation
    - use of a FQDN and https
    - length of paths
    - presence of documentation

    :param swagger: the swagger spec
    :return: a list of errors
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
