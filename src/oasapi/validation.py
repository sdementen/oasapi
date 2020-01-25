"""Swagger 2.0 validation

see https://github.com/swagger-api/swagger-editor/tree/master/src/plugins/validate-semantic
for semantic rules (i.e. beyond teh JSONSchema validation of the swagger)"""
import json
import numbers
import re
from itertools import groupby
from pathlib import Path
from typing import Set, Dict

from jsonpath_ng import parse, Union
from jsonschema import Draft4Validator

from oasapi.common import get_elements, OPERATIONS_LOWER, REFERENCE_SECTIONS
from .events import (
    ReferenceNotFoundValidationError,
    ParameterDefinitionValidationError,
    SecurityDefinitionNotFoundValidationError,
    OAuth2ScopeNotFoundInSecurityDefinitionValidationError,
    DuplicateOperationIdValidationError,
    JsonSchemaValidationError,
    ValidationError,
    ReferenceInvalidSyntax,
    ReferenceInvalidSection,
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
    """Check a parameter structure

    For a parameter, the check for consistency are on:
    - required and default
    - type/format and default
    - enum
    """
    events = set()

    name = param.get("name", "unnamed-parameter")
    required = param.get("required", False)
    default = param.get("default")
    _type = param.get("type")
    format = param.get("format")
    enum = param.get("enum")

    # check if required=True and default are both given
    if required and default is not None:
        events.add(
            ParameterDefinitionValidationError(
                path=path_param,
                reason=f"The parameter is required yet it has a default value",
                parameter_name=name,
            )
        )

    # check if type==array that there is an items
    if _type == "array" and "items" not in param:
        events.add(
            ParameterDefinitionValidationError(
                path=path_param,
                reason=f"The parameter is of type 'array' but is missing an 'items' field",
                parameter_name=name,
            )
        )

    # check enum does not contain duplicates
    if enum:
        if len(set(enum)) != len(enum):
            events.add(
                ParameterDefinitionValidationError(
                    path=path_param + ("enum",),
                    reason=f"The enum values {enum} contains duplicate values",
                    parameter_name=name,
                )
            )
        if default is not None and default not in enum:
            events.add(
                ParameterDefinitionValidationError(
                    path=path_param + ("default",),
                    reason=f"The default value {repr(default)} is not one of the enum values {enum}",
                    parameter_name=name,
                )
            )

    # check type/format & default value in accordance with type/format
    # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#data-types
    map_type2subtypes_pythontype = {
        ("string", None): str,
        ("string", "byte"): re.compile(
            r"^(?:[A-Za-z0-9+/\s]{4})*(?:[A-Za-z0-9+/\s]{2}==|[A-Za-z0-9+/\s]{3}=)?$"
        ),
        ("string", "binary"): str,
        ("string", "date"): re.compile(r"^([0-9]+)-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])$"),
        ("string", "dateTime"): re.compile(
            r"^([0-9]+)-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])"  # date
            r"[Tt]"
            r"([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9]|60)(\.[0-9]+)?"  # time
            r"(([Zz])|([+|\-]([01][0-9]|2[0-3]):[0-5][0-9]))$"  # offset
        ),
        ("string", "password"): str,
        ("integer", None): numbers.Integral,
        ("integer", "int32"): numbers.Integral,
        ("integer", "int64"): numbers.Integral,
        ("number", None): numbers.Real,
        ("number", "float"): numbers.Real,
        ("number", "double"): numbers.Real,
        ("boolean", None): bool,
        ("array", None): list,
    }
    if default is not None and _type:
        regexp_or_type = map_type2subtypes_pythontype.get((_type, format))
        # if no match with both _type, format, check if match only on _type (format being freeform)
        if not regexp_or_type:
            regexp_or_type = map_type2subtypes_pythontype.get((_type, None))

        if regexp_or_type:
            # the type & format matches one of the Swagger Specifications documented type & format combinations
            # we can check the default format

            # decompose regexp_or_type into type and RE expression
            if isinstance(regexp_or_type, type):
                # regexp_or_type is a standard python type
                re_pattern = None
                py_type = regexp_or_type
            else:
                # regexp_or_type is a regexp expression
                re_pattern = regexp_or_type
                py_type = str

            if not isinstance(default, py_type):
                events.add(
                    ParameterDefinitionValidationError(
                        path=path_param + ("default",),
                        reason=f"The default value {repr(default)} is not of the expected type '{_type}'",
                        parameter_name=name,
                    )
                )

            # if a regexp matching string is expected
            if re_pattern is not None:
                if not (isinstance(default, str) and re_pattern.match(default)):
                    events.add(
                        ParameterDefinitionValidationError(
                            path=path_param + ("default",),
                            reason=f"The default value '{default}' does not conform to the string format '{format}'",
                            parameter_name=name,
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
    events = set()

    ref_jspath = parse("$..'$ref'")

    for _, reference, path in get_elements(swagger, ref_jspath):
        # handle only local references
        if reference.startswith("#/"):
            # decompose reference (error if not possible)
            try:
                rt, obj = reference[2:].split("/")
            except ValueError:
                events.add(
                    ReferenceInvalidSyntax(
                        path=path, reason=f"reference {reference} not of the form '#/section/item'"
                    )
                )
                continue

            if rt not in REFERENCE_SECTIONS:
                events.add(
                    ReferenceInvalidSection(
                        path=path,
                        reason=f"Reference {reference} not referring to one of the sections {REFERENCE_SECTIONS}",
                    )
                )

            # resolve reference (error if not possible)
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
                        reason=f"the operationId '{opId}' is already used in an endpoint.",
                        operationId=opId,
                    )
                )

    return events


def check_schema(swagger: Dict) -> Set[ValidationError]:
    """Check swagger is compliant with schema"""
    # validate the json schema of the swagger_lib
    schema = json.load((Path(__file__).parent / "schemas" / "schema_swagger.json").open())
    v = Draft4Validator(schema)

    return {
        JsonSchemaValidationError(path=tuple(error.absolute_path), reason=error.message)
        for error in v.iter_errors(swagger)
    }


def validate(swagger: Dict) -> Set[ValidationError]:
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

    errors = (
        check_schema(swagger)
        | check_references(swagger)
        | check_security(swagger)
        | check_parameters(swagger)
        | detect_duplicate_operationId(swagger)
    )

    return errors
