import logging
import re

# list of verbs that are valid in an OpenAPI/Swagger
from functools import singledispatch

from jsonpath_ng import Fields, Index, DatumInContext, Child, parse, Union

OPERATIONS_LIST = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "HEAD"]
OPERATIONS = set(OPERATIONS_LIST)
OPERATIONS_LOWER = [op.lower() for op in OPERATIONS_LIST]  # ordered list of operations
# regexp to match verbs
OPERATIONS_RE = re.compile("|".join(OPERATIONS), re.IGNORECASE)

REFERENCE_SECTIONS = ["definitions", "responses", "parameters"]

# list of JSPATH for different structures
JSPATH_ENDPOINTS = parse(f"paths.*")
JSPATH_OPERATIONS = parse(f"paths.*.({'|'.join(OPERATIONS_LOWER)})")

JSPATH_SECURITY_GLOBAL = parse("security.[*].*")
JSPATH_SECURITY_OPERATION = parse(f"paths.*.({'|'.join(OPERATIONS_LOWER)}).security.[*].*")
# print(JSPATH_OPERATIONS)
# print(JSPATH_SECURITY_GLOBAL)
# print(Child(JSPATH_OPERATIONS,JSPATH_SECURITY_GLOBAL))

JSPATH_SECURITY = Union(JSPATH_SECURITY_GLOBAL, JSPATH_SECURITY_OPERATION)

JSPATH_PARAMETERS_GLOBAL = parse("parameters.[*]")
JSPATH_PARAMETERS_PATH = parse(f"paths.*.parameters.[*]")
JSPATH_PARAMETERS_OPERATION = parse(f"paths.*.({'|'.join(OPERATIONS_LOWER)}).parameters.[*]")
JSPATH_PARAMETERS = Union(
    JSPATH_PARAMETERS_GLOBAL, Union(JSPATH_PARAMETERS_PATH, JSPATH_PARAMETERS_OPERATION)
)
JSPATH_PATHS_REFERENCES = parse("paths..'$ref'")
JSPATH_REFERENCES = parse("$..'$ref'")
JSPATH_OPERATIONID = parse(f"paths.*.({'|'.join(OPERATIONS_LOWER)}).operationId")
JSPATH_COMPONENTS = parse(f"$.({'|'.join(REFERENCE_SECTIONS)}).*")

logger = logging.getLogger(__file__)


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
def tuple_path(o):  # pragma: no cover
    """Return the path of a JSONPath object as a tuple"""
    raise NotImplementedError


@tuple_path.register(Fields)
def _(o):
    return o.fields


@tuple_path.register(Child)
def _(o):  # pragma: no cover
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


JSPATH_TAGS = parse("tags.[*].name")
JSPATH_OPERATION_TAGS = parse(f"paths.*.({'|'.join(OPERATIONS_LOWER)}).tags")
