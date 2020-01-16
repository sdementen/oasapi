import logging
import re

# list of verbs that are valid in an OpenAPI/Swagger
from functools import singledispatch

from jsonpath_ng import Fields, Index, DatumInContext, Child

OPERATIONS_LIST = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "HEAD"]
OPERATIONS = set(OPERATIONS_LIST)
OPERATIONS_LOWER = [op.lower() for op in OPERATIONS_LIST]  # ordered list of operations
# regexp to match verbs
OPERATIONS_RE = re.compile("|".join(OPERATIONS), re.IGNORECASE)

logger = logging.getLogger(__file__)

KEY_VALIDATION = {
    "security": lambda path: (not path) or (path[0] == "paths" and len(path) == 3),
    "parameters": lambda path: (not path) or (path[0] == "paths" and 2 <= len(path) <= 3),
    "$ref": lambda path: True,
    "operationId": lambda path: len(path) == 3
    and path[0] == "paths"
    and OPERATIONS_RE.match(path[2]),
}


def find_keys(d, key, path=()):
    """Find keys with a given value (e.g. operationId, ...) and return it with the paths.
    It checks that the key is in the right location in the swagger (e.g. an operationId can only be found in paths/xxx/xxx/operationId).

    key should be one of ('security', 'parameters', '$ref', 'operationId')
    """
    if isinstance(d, list):
        for i, e in enumerate(d):
            yield from find_keys(e, key, path + (i,))
    elif isinstance(d, dict):
        if key in d:
            assert key in KEY_VALIDATION, f"Key '{key}' not yet handled in 'find_keys'"
            if KEY_VALIDATION[key](path):
                yield d[key], path

        for k, v in d.items():
            yield from find_keys(v, key, path + (k,))


def extract_references(specs_part):
    """reference_type in definitions/responses => return sets of references used"""
    return {tuple(key[2:].split("/")) + (path,) for key, path in find_keys(specs_part, "$ref")}


# Return the longest prefix of all list elements.
def commonprefix(m):
    """Given a list of pathnames, returns the longest common leading component without trailing /"""
    if not m:
        return ""
    m = [p.rstrip("/").split("/") for p in m]

    s1 = min(m)
    s2 = max(m)

    s = s1
    for i, (c1, c2) in enumerate(zip(s1, s2)):
        if c1 != c2:
            s = s1[:i]
            break

    return "/".join(s)


def get_elements(dct, jspth):
    """Return tuples of (key, value, tuple_path) in the dict dct with keys according to the JSON path jspth"""
    for elem in jspth.find(dct):
        yield str(elem.path), elem.value, tuple_path(elem)


@singledispatch
def tuple_path(o):
    """Return the path of a JSONPath object as a tuple"""
    raise NotImplementedError


@tuple_path.register(Fields)
def _(o):
    return o.fields


@tuple_path.register(Child)
def _(o):
    return tuple_path(o.left) + tuple_path(o.right)


@tuple_path.register(Index)
def _(o):
    return (f"[{o.index}]",)


@tuple_path.register(DatumInContext)
def _(o):
    if o.context:
        return tuple_path(o.context) + tuple_path(o.path)
    else:
        return ()
