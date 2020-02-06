import copy
import re
from functools import reduce
from typing import Dict, Tuple, List

import deepmerge
from attr import dataclass

from oasapi.common import get_elements, JSPATH_OPERATIONS
from oasapi.events import FilterAction


@dataclass
class FilterCondition:
    tags: List[str] = None
    operations: List[str] = None
    security_scopes: List[str] = None

    _operations_re = None

    def __attrs_post_init__(self):
        # def __post_init__(self): # for dataclasses
        if self.operations:
            # store compiled version of regex expressions
            self._operations_re = [re.compile(op, re.IGNORECASE) for op in self.operations]


def filter(
    swagger: Dict, mode="keep_only", conditions=List[FilterCondition]
) -> Tuple[Dict, List[FilterAction]]:
    """
    Filter endpoints of a swagger specification.

    The endpoints can be filtered according to two modes:
    - keep_only: it will keep only the operations matching any of the conditions
    - remove: it will remove only the operations matching any of the conditions

    The conditions parameter is a list of FilterCondition objects containing each:
    - tags: the operation is kept/removed only if it has at least one tag in the tags
    - operations: the operation is kept/removed only if its VERB + PATH matches at least one operation in the operations
    - security_scopes: the operation is kept/removed only if it is protected by at least one security with a scope in the security_scopes
    Any of these fields can be None to avoid matching on the field criteria.

    :param mode:
    :param conditions:
    :param swagger: the swagger spec
    :return: filtered swagger, a set of actions
    """
    swagger = copy.deepcopy(swagger)

    filter = generate_filter_conditions(conditions, merge_matches=True)

    # resolve security to have each operation have the proper security
    # after having already filtered/matched the security against the conditions
    # todo: resulting swagger has global security spread over all paths due to resolving
    #       it should be cleaned afterwards to keep the original approach...
    #       Maybe add this to the "prune" operation (factorize security) ?
    if "security" in swagger and filter.on_security_scopes_useful:
        match = filter((), swagger, on_tags=False, on_operations=False)
        if match:
            swagger = match
        else:
            del swagger["security"]

        resolve_security(swagger)

    # get operations to keep
    operations_to_remove = {
        path: filter(path, operation)
        for key, operation, path in get_elements(swagger, JSPATH_OPERATIONS)
    }
    # update the paths
    paths = swagger["paths"]
    for (_, path, verb), new_value in operations_to_remove.items():
        if new_value:
            paths[path][verb] = new_value
        else:
            del paths[path][verb]

    return swagger, []


def append_no_duplicate(config, path, base, nxt):
    """ a list strategy to append only the elements not yet in the list."""
    for e in nxt:
        if e not in base:
            base.append(e)
    return base


# merger object to merge dict with list in a recursive way
# with a strategy for list to avoid duplicates
m = deepmerge.Merger(
    # pass in a list of tuple, with the
    # strategies you are looking to apply
    # to each type.
    [(list, [append_no_duplicate]), (dict, ["merge"])],
    # next, choose the fallback strategies,
    # applied to all other types:
    ["override"],
    # finally, choose the strategies in
    # the case where the types conflict:
    ["override"],
)


def generate_filter_conditions(conditions: List[FilterCondition], merge_matches=False):
    """Return a function:
     - taking an operation (as a dict) as well as three flags:
        - on_tags (default = True)
        - on_operations (default = True)
        - on_security_scopes (default = True)
     - returning
        - False if the operation does not match the condition
        - the operation (modified to match the condition) if it matched a condition

    The flags on_XXX specifies if the given criteria should be actively matched or not (it is useful
    if one wants to selectively filter according to criterias while keepîng the same conditions.

    The flag merge_matches drives the behavior of the operation matching and adaptation.
    When an operation is matched to a condition, the operation will be adapted to the condition.
    For instance, if a condition has a tags=["tag1"] and the operation has tags=["tag1","tag2"], it
    will be matched by this condition and the operation is transformed to only have tags=["tag1"].

    When we have multiple conditions matching the same operation, the operation will be tranformed differently
    for each condition. If the flag merge_matches is False, it will return the operation transformed by the
    firtst matching conditions (or False if none of the conditions match the operation). If the flag
    merge_matches is True, all conditions will be tested on the operations and the transformations of the operation
    for each matching conditions will be merged.
    For example, if we have an operation with tags=["tag1","tag2","tag3"] and
     two conditions [FilterCondition(tags=["tag1"]),  FilterCondition(tags=["tag2"])], with
      - flag_matches=False, the resulting operation will have ["tag1"] (as first match is on tag1)
      - flag_matches=True,  the resulting operation will have ["tag1","tag2"] (as both conditions matches,
        each returning its operation transformed, i.e. ["tag1"] for the first and ["tag2"] for the second,
        and the results are merged in a single operation, giving ["tag1","tag2"]

    """

    def generate_filter(condition: FilterCondition):
        """Return a function taking an operation dict and returning True/False if the operation match the condition.

        The condition is a dict with keys tags, operations, security_scopes"""

        def filter(path: Tuple, operation: Dict, on_tags, on_security_scopes, on_operations):
            # deep copy the operation as it will be changed
            operation = copy.deepcopy(operation)

            # check tags
            if on_tags and condition.tags is not None:
                # ensure the operation has at least one of the condition tags and filter on it
                original_tags = operation.get("tags")
                if original_tags is None:
                    # the operation has not tags while the condition requires tags
                    return False
                filtered_tags = [tag for tag in original_tags if tag in condition.tags]
                if not filtered_tags:
                    # no tags matches with the conditions
                    return False

                # adapt the operation to only have the filtered tags
                operation["tags"] = filtered_tags

            # check operations
            if on_operations and condition.operations is not None:
                # ensure the operation has at least one of the condition operations and filter on it
                # if re.match(condition.operations)
                _, endpoint, verb = path
                str_to_match = f"{verb} {endpoint}"
                if not any(re_op.match(str_to_match) for re_op in condition._operations_re):
                    return False

            # check security_scopes
            if on_security_scopes and condition.security_scopes is not None:
                # ensure the operation has at least one of the condition security scopes and filter on it
                original_security = operation.get("security")
                if original_security is None:
                    # the operation has not security_scopes while the condition requires security_scopes
                    return False
                # keep only securities that contains sec_def with at least one scope in the security_scopes
                filtered_security = [
                    {
                        sec_def: [scope for scope in scopes if scope in condition.security_scopes]
                        for sec_def, scopes in security.items()
                    }
                    for security in original_security
                ]
                # remove sec_def with no scopes
                filtered_security = [
                    {sec_def: scopes for sec_def, scopes in security.items() if scopes}
                    for security in filtered_security
                ]
                # remove empty security
                filtered_security = [security for security in filtered_security if security]
                if not filtered_security:
                    # no security_scopes matches with the conditions
                    return False

                # adapt the operation to only have the filtered security_scopes
                operation["security"] = filtered_security

            # default True
            return operation

        return filter

    # check if some criteria are never defined
    on_tags_useful = any(condition.tags is not None for condition in conditions)
    on_operations_useful = any(condition.operations is not None for condition in conditions)
    on_security_scopes_useful = any(
        condition.security_scopes is not None for condition in conditions
    )
    # no filter on tags or security_scopes, merge is not necessary
    # as operation are not transformed by operations criteria
    if not (on_tags_useful or on_security_scopes_useful):
        merge_matches = False

    # generate filters from conditions
    _filters = [generate_filter(condition) for condition in conditions]

    def filter_all(
        path,
        operation,
        *,
        on_tags=on_tags_useful,
        on_security_scopes=on_security_scopes_useful,
        on_operations=on_operations_useful,
    ):
        # check a operation to see if match any of the filter
        # first trueish filter returned if not merge_matches
        # else append them in operations that will be merged afterwards
        operations = []
        for _filter in _filters:
            fvalue = _filter(path, operation, on_tags, on_security_scopes, on_operations)
            if fvalue is not False:
                if merge_matches:
                    operations.append(fvalue)
                else:
                    return fvalue

        # if operations is not empty, it means we had some matches
        # and that merge_matches is True => merge the operations in a single one
        if operations:
            return reduce(m.merge, operations)

        return False

    # assign flags if useful
    filter_all.on_security_scopes_useful = on_security_scopes_useful
    filter_all.on_tags_useful = on_tags_useful
    filter_all.on_operations_useful = on_operations_useful

    return filter_all


def resolve_security(swagger):
    """Resolve security in swagger (in place)

    Apply the global security if defined to each operation when the latter has no security defined
    """
    # resolve security at global level to operation level
    global_security = swagger.get("security")

    if global_security is not None:
        for key, value, path in get_elements(swagger, JSPATH_OPERATIONS):
            value.setdefault("security", global_security)
