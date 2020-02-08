import copy
import re
from functools import reduce
from typing import Dict, Tuple, List, Set

import deepmerge
from attr import dataclass

from oasapi.common import get_elements, JSPATH_OPERATIONS
from oasapi.events import FilterAction, OperationRemovedFilterAction, OperationChangedFilterAction


@dataclass
class FilterCondition:
    tags: Set[str] = None
    operations: List[str] = None
    security_scopes: Set[str] = None

    _operations_re = None

    def __attrs_post_init__(self):  # def __post_init__(self): # for dataclasses

        # convert tags/security_scopes attributes to sets
        if self.tags:
            self.tags = set(self.tags)
        if self.security_scopes:
            self.security_scopes = set(self.security_scopes)

        # do not convert operations to set to keep order of filtering
        if self.operations:
            # store compiled version of regex expressions
            self._operations_re = [
                re.compile(op.rstrip("$") + "$", re.IGNORECASE) for op in self.operations
            ]


def filter(
    swagger: Dict, mode="keep_only", conditions: List[FilterCondition] = None
) -> Tuple[Dict, List[FilterAction]]:
    """
    Filter endpoints of a swagger specification.

    The endpoints can be filtered according to two modes:

    - keep_only: it will keep only the operations matching any of the conditions
    - remove: it will remove only the operations matching any of the conditions (TO BE IMPLEMENTED)

    The conditions parameter is a list of FilterCondition objects containing each:

    - tags: the operation is kept only if it has at least one tag in the tags
    - operations: the operation is kept only if its VERB + PATH matches at least one operation in the operations
    - security_scopes: the operation is kept only if it requires no security or if some of its security items only requires
      the scopes in the security_scopes
    Any of these fields can be None to avoid matching on the field criteria.

    :param mode:
    :param conditions:
    :param swagger: the swagger spec
    :return: filtered swagger, a set of actions
    """
    if mode != "keep_only":
        raise NotImplementedError(f"The mode '{mode}' is not yet implemented.")

    if conditions is None:
        return swagger, []

    swagger = copy.deepcopy(swagger)

    global_security = swagger.get("security")
    filter = generate_filter_conditions(
        conditions, merge_matches=True, global_security=global_security
    )

    # if global security defined, filter it also
    if global_security is not None and filter.on_security_scopes_useful:
        match = filter((), swagger, on_tags=False, on_operations=False)
        if match:
            swagger = match
        else:
            # TODO: as the global security does not match with the conditions
            #       we could already remove from the paths all operations with no
            #       security defined (optimization trick)
            del swagger["security"]

    # get operations to keep
    operations_to_keep = {
        path: filter(path, operation)
        for key, operation, path in get_elements(swagger, JSPATH_OPERATIONS)
    }
    # update the paths
    actions = []
    paths = swagger["paths"]
    for path, new_value in operations_to_keep.items():
        (_, endpoint, verb) = path
        if new_value is not False:
            if paths[endpoint][verb] != new_value:
                actions.append(
                    OperationChangedFilterAction(
                        path=path, reason="The operation has been modified by a filter."
                    )
                )
                paths[endpoint][verb] = new_value
        else:
            actions.append(
                OperationRemovedFilterAction(
                    path=path,
                    reason="The operation has been removed as it does not match any filter.",
                )
            )
            del paths[endpoint][verb]

    return swagger, actions


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


def generate_filter_conditions(
    conditions: List[FilterCondition], merge_matches=False, global_security=None
):
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
        :param global_security:

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
                # ensure the operation requires only the condition security scopes (or is open) and filter on it
                original_security = operation.get("security", global_security)

                if original_security is not None:
                    # the endpoint is secured
                    # keep only securities with all scopes for each sec_def in the security_scopes
                    filtered_security = [
                        security
                        for security in original_security
                        if all(
                            condition.security_scopes.issuperset(scopes)
                            for sec_def, scopes in security.items()
                        )
                    ]
                    # for each filtered security, ensure # remove sec_def with no scopes
                    # filtered_security = [
                    #     {sec_def: scopes for sec_def, scopes in security.items() if scopes}
                    #     for security in filtered_security
                    # ]
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
