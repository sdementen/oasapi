from jsonpath_ng import parse, Union, Child

from oasapi.common import OPERATIONS_LOWER, REFERENCE_SECTIONS

# list of JSPATH for different structures

JSPATH_INFO = parse(f"info")
JSPATH_ENDPOINTS = parse(f"paths.*")
JSPATH_OPERATIONS = Child(JSPATH_ENDPOINTS, parse(f"({'|'.join(OPERATIONS_LOWER)})"))
JSPATH_OPERATION_RESPONSES = Child(JSPATH_OPERATIONS, parse("responses"))
JSPATH_OPERATIONID = Child(JSPATH_OPERATIONS, parse("operationId"))
JSPATH_OPERATION_TAGS = Child(JSPATH_OPERATIONS, parse(f"tags"))
JSPATH_SECURITY_OPERATION = Child(JSPATH_OPERATIONS, parse("security.[*].*"))
JSPATH_SECURITY_GLOBAL = parse("security.[*].*")
JSPATH_SECURITY = Union(JSPATH_SECURITY_GLOBAL, JSPATH_SECURITY_OPERATION)
JSPATH_PARAMETERS_GLOBAL = parse("parameters.[*]")
JSPATH_PARAMETERS_PATH = parse(f"paths.*.parameters.[*]")
JSPATH_PARAMETERS_OPERATION = Child(JSPATH_OPERATIONS, parse("parameters.[*]"))
JSPATH_PARAMETERS = Union(
    JSPATH_PARAMETERS_GLOBAL, Union(JSPATH_PARAMETERS_PATH, JSPATH_PARAMETERS_OPERATION)
)
JSPATH_PATHS_REFERENCES = parse("paths..'$ref'")
JSPATH_REFERENCES = parse("$..'$ref'")
JSPATH_COMPONENTS = parse(f"$.({'|'.join(REFERENCE_SECTIONS)}).*")
JSPATH_TAGS = parse("tags.[*].name")
