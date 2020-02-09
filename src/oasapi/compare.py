import itertools
from typing import Dict, Tuple, List

from oasapi.common import get_elements
from oasapi.events import (
    DiffAction,
    AddedOperationDiffAction,
    RemovedDeprecatedOperationDiffAction,
    RemovedNotDeprecatedOperationDiffAction,
    DeprecatedOperationDiffAction,
)
from oasapi.jspaths import JSPATH_OPERATIONS


def compare_paths(swagger_from: Dict, swagger_to: Dict) -> List[DiffAction]:
    """Compare the paths of both swaggers"""
    operations_from = {
        pth: value for _, value, pth in get_elements(swagger_from, JSPATH_OPERATIONS)
    }
    operations_from_paths = set(operations_from)
    operations_to = {pth: value for _, value, pth in get_elements(swagger_to, JSPATH_OPERATIONS)}
    operations_to_paths = set(operations_to)

    # add/removal/noop operations
    operations_added = operations_to_paths.difference(operations_from_paths)
    operations_removed = operations_from_paths.difference(operations_to_paths)
    operations_staying = operations_from_paths.intersection(operations_to_paths)

    # for removed operations, check with were deprecated before
    operations_removed_deprecated = set(
        op for op in operations_removed if operations_from[op].get("deprecated", False)
    )
    operations_removed_not_deprecated = operations_removed.difference(operations_removed_deprecated)

    # for staying operations, check which have been deprecated
    operations_staying_depracated = set(
        op
        for op in operations_staying
        if not operations_from[op].get("deprecated", False)
        and operations_to[op].get("deprecated", False)
    )

    # generate actions following the original order of the operations in the swaggers
    # (reason why the use of  'for op in operations_to if op in operations_added'
    # instead of the simpler 'for op in operations_added')
    actions = (
        [
            AddedOperationDiffAction(path=op, reason="The operation has been added")
            for op in operations_to
            if op in operations_added
        ]
        + [
            RemovedDeprecatedOperationDiffAction(
                path=op, reason="The operation was deprecated and has been removed"
            )
            for op in operations_from
            if op in operations_removed_deprecated
        ]
        + [
            RemovedNotDeprecatedOperationDiffAction(
                path=op, reason="The operation was not yet deprecated but has been removed"
            )
            for op in operations_from
            if op in operations_removed_not_deprecated
        ]
        + [
            DeprecatedOperationDiffAction(path=op, reason="The operation has been deprecated")
            for op in operations_to
            if op in operations_staying_depracated
        ]
    )
    return actions


def compare(swagger: Dict, swagger_new: Dict) -> Tuple[Dict, List[DiffAction]]:
    """
    Compare two swagger specifications.

    The comparison covers:

    - add/removal/deprecation of operations
    - [todo] change in response/request
    - [todo] change in securities
    - [todo - low priority] change in documentation, tags

    :param swagger: the base swagger spec
    :param swagger_new: the swagger spec to compare to the base
    :return: a set of diff actions
    """

    actions = list(itertools.chain(*[compare_paths(swagger, swagger_new)]))
    return swagger_new, actions
