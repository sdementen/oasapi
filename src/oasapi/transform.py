from collections import defaultdict

from jsonpath_ng import parse, Union

from oasapi.common import get_elements, REFERENCE_SECTIONS, OPERATIONS_LOWER
from oasapi.events import (
    ReferenceNotUsedFilterAction,
    SecurityDefinitionNotUsedAction,
    OAuth2ScopeNotUsedAction,
)


def prune_unused_global_items(swagger):
    """Prune the swagger (in place) of its unused global items
    in the definitions, responses and paremeters global sections"""

    def decompose_reference(references):
        return set(
            tuple(reference[2:].split("/"))
            for _, reference, _ in references
            if reference.startswith("#/")
        )

    # start by taking all references use in /paths
    refs = refs_new = decompose_reference(get_elements(swagger, parse("$.paths..'$ref'")))

    ref_jspath = parse("$..'$ref'")

    while True:
        swagger_new = {section: {} for section in REFERENCE_SECTIONS}
        for rt, obj in refs_new:
            # handle only local references
            swagger_new[rt][obj] = swagger[rt][obj]

        refs_new = decompose_reference(get_elements(swagger_new, ref_jspath))

        if refs_new.issubset(refs):
            break

        refs |= refs_new

    actions = []
    for _, _, ref_path in get_elements(swagger, parse(f"$.({'|'.join(REFERENCE_SECTIONS)}).*")):
        if ref_path not in refs:
            # the reference is not used, remove it
            rt, obj = ref_path
            del swagger[rt][obj]
            actions.append(
                ReferenceNotUsedFilterAction(path=(rt, obj), reason="reference not used")
            )

    return swagger, actions


def prune_unused_security_definitions(swagger):
    """Prune the swagger (in place) of its unused securityDefinitions or oauth scopes"""
    if "securityDefinitions" not in swagger:
        return swagger, []

    security_jspath = Union(
        parse("security.[*].*"), parse(f"paths.*.({'|'.join(OPERATIONS_LOWER)}).security.[*].*")
    )

    # detect security definitions used and for which scope
    secdefs_used = defaultdict(set)
    for sec_name, sec_scopes, _ in get_elements(swagger, security_jspath):
        secdefs_used[sec_name].update(sec_scopes)

    # iterate existing securityDefinitions to check if they are used and if their scopes are used
    actions = []
    for sec_name, sec_def in swagger["securityDefinitions"].copy().items():
        if sec_name not in secdefs_used:
            del swagger["securityDefinitions"][sec_name]
            actions.append(
                SecurityDefinitionNotUsedAction(
                    path=("securityDefinitions", sec_name), reason="security definition not used"
                )
            )

        if "scopes" in sec_def:
            for scope_name, scope_def in sec_def["scopes"].copy().items():
                if scope_name not in secdefs_used[sec_name]:
                    del swagger["securityDefinitions"][sec_name]["scopes"][scope_name]
                    actions.append(
                        OAuth2ScopeNotUsedAction(
                            path=("securityDefinitions", sec_name, "scopes", scope_name),
                            reason="oauth2 scope not used",
                        )
                    )

    return swagger, actions
