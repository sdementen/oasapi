import copy
import itertools
from collections import defaultdict
from typing import Dict, Tuple, List

from oasapi.common import (
    get_elements,
    REFERENCE_SECTIONS,
    JSPATH_PATHS_REFERENCES,
    JSPATH_REFERENCES,
    JSPATH_COMPONENTS,
    JSPATH_TAGS,
    JSPATH_OPERATION_TAGS,
    JSPATH_SECURITY,
    JSPATH_ENDPOINTS,
)
from oasapi.events import (
    ReferenceNotUsedFilterAction,
    SecurityDefinitionNotUsedFilterAction,
    OAuth2ScopeNotUsedFilterAction,
    TagNotUsedFilterAction,
    FilterAction,
    PathsEmptyFilterError,
)


def prune_unused_global_items(swagger):
    """Prune the swagger (in place) of its unused global items
    in the definitions, responses and parameters global sections"""

    def decompose_reference(references):
        return set(
            tuple(reference[2:].split("/"))
            for _, reference, _ in references
            if reference.startswith("#/")
        )

    # start by taking all references use in /paths
    refs = refs_new = decompose_reference(get_elements(swagger, JSPATH_PATHS_REFERENCES))

    while True:
        swagger_new = {section: {} for section in REFERENCE_SECTIONS}
        for rt, obj in refs_new:
            # handle only local references
            swagger_new[rt][obj] = swagger[rt][obj]

        refs_new = decompose_reference(get_elements(swagger_new, JSPATH_REFERENCES))

        if refs_new.issubset(refs):
            break

        refs |= refs_new

    actions = []
    for _, _, ref_path in get_elements(swagger, JSPATH_COMPONENTS):
        if ref_path not in refs:
            # the reference is not used, remove it
            rt, obj = ref_path
            del swagger[rt][obj]
            actions.append(
                ReferenceNotUsedFilterAction(path=(rt, obj), reason="reference not used")
            )

    # remove sections that are left empty
    for section in REFERENCE_SECTIONS:
        if section in swagger and not swagger[section]:
            del swagger[section]

    return swagger, actions


def prune_unused_security_definitions(swagger):
    """Prune the swagger (in place) of its unused securityDefinitions or oauth scopes"""
    if "securityDefinitions" not in swagger:
        return swagger, []

    security_jspath = JSPATH_SECURITY

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
                SecurityDefinitionNotUsedFilterAction(
                    path=("securityDefinitions", sec_name), reason="security definition not used"
                )
            )

        elif "scopes" in sec_def:
            for scope_name, scope_def in sec_def["scopes"].copy().items():
                if scope_name not in secdefs_used[sec_name]:
                    del swagger["securityDefinitions"][sec_name]["scopes"][scope_name]
                    actions.append(
                        OAuth2ScopeNotUsedFilterAction(
                            path=("securityDefinitions", sec_name, "scopes", scope_name),
                            reason="oauth2 scope not used",
                        )
                    )

    # remove securityDefinitions if empty
    if not swagger["securityDefinitions"]:
        del swagger["securityDefinitions"]

    return swagger, actions


def prune_unused_tags(swagger):
    """Prune the swagger (in place) of its unused tags"""
    if "tags" not in swagger:
        return swagger, []

    tags_jspath = JSPATH_OPERATION_TAGS

    # detect security definitions used and for which scope
    tags_used = set().union(*[tags_list for _, tags_list, _ in get_elements(swagger, tags_jspath)])

    # iterate existing securityDefinitions to check if they are used and if their scopes are used
    actions = []
    for _, tag_name, (*path_before_name, path_name) in get_elements(swagger, JSPATH_TAGS):
        if tag_name not in tags_used:
            actions.append(
                TagNotUsedFilterAction(
                    path=tuple(path_before_name), reason=f"tag definition for '{tag_name}' not used"
                )
            )

    swagger["tags"] = [tag for tag in swagger["tags"] if tag["name"] in tags_used]

    # remove tags if empty
    if not swagger["tags"]:
        del swagger["tags"]

    return swagger, actions


def prune_empty_paths(swagger):
    """Prune the swagger (in place) of its empty paths (ie paths with no verb)"""

    # list all operations (paths without any operation are not included
    actions = []
    for endpoint_name, endpoint, path in get_elements(swagger, JSPATH_ENDPOINTS):
        if not endpoint or len(endpoint) == 1 and "parameters" in endpoint:
            # endpoint is empty, remove it
            del swagger["paths"][endpoint_name]

            actions.append(
                PathsEmptyFilterError(
                    path=path, reason=f"path '{endpoint_name}' has no operations defined"
                )
            )

    return swagger, actions


def prune(swagger: Dict) -> Tuple[Dict, List[FilterAction]]:
    """
    Prune a swagger specification.

    The pruning removed from the swagger the following elements:

    - unused global definitions/responses/parameters
    - unused securityDefinition/scopes
    - unused tags
    - empty paths (i.e. endpoints with no verbs)


    :param swagger: the swagger spec
    :return: pruned swagger, a set of actions
    """
    swagger = copy.deepcopy(swagger)
    actions = list(
        itertools.chain(
            *[
                prune_operation(swagger)[1]
                for prune_operation in [
                    prune_empty_paths,
                    prune_unused_tags,
                    prune_unused_global_items,
                    prune_unused_security_definitions,
                ]
            ]
        )
    )

    return swagger, actions
