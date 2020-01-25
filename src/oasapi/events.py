from typing import Iterable, Union, Dict, Tuple

from attr import dataclass

#: the type of a swagger path
SwaggerPath = Tuple[Union[int, str], ...]


@dataclass(frozen=True)
class Event:
    """Base class for an event (an error, an action, ...).
    """

    #: the path in the dictionary to which the even relates
    path: SwaggerPath

    #: the reason of the event
    reason: str

    #: the string representation of the type of event
    type: str

    @staticmethod
    def format_path(path: SwaggerPath) -> str:
        """Format a path to a JSON Path alike string"""
        return ".".join(map(str, path))


@dataclass(frozen=True)
class Action(Event):
    type: str


@dataclass(frozen=True)
class Error(Event):
    """Base class for an error
    """

    pass


@dataclass(frozen=True)
class Warning(Event):
    type: str


@dataclass(frozen=True)
class FilterError(Error):
    pass


@dataclass(frozen=True)
class FilterWarning(Warning):
    pass


@dataclass(frozen=True)
class ValidationError(Error):
    """Base class for a validation error (used in the swagger validation)
    """

    pass


@dataclass(frozen=True)
class FilterAction(Action):
    pass


@dataclass(frozen=True)
class ValidationAction(Action):
    pass


@dataclass(frozen=True)
class ReferenceNotFoundFilterError(FilterError):
    type: str = "Reference not found"


@dataclass(frozen=True)
class PathsEmptyFilterError(FilterError):
    type: str = "Paths are empty"


@dataclass(frozen=True)
class ReferenceNotUsedFilterAction(FilterAction):
    type: str = "Reference filtered out"


@dataclass(frozen=True)
class SecurityDefinitionNotUsedFilterAction(FilterAction):
    type: str = "Security definition removed"


@dataclass(frozen=True)
class OAuth2ScopeNotUsedFilterAction(FilterAction):
    type: str = "Oauth2 scope removed"


@dataclass(frozen=True)
class TagNotUsedFilterAction(FilterAction):
    type: str = "Tag definition removed"


@dataclass(frozen=True)
class EndpointRenamedFilterAction(FilterAction):
    old_path: str
    new_path: str
    type: str = "Endpoint renamed by regexp"


@dataclass(frozen=True)
class EndpointsReplacedFilterAction(FilterAction):
    new_paths: Dict
    type: str = "All paths are replaced by explicit paths from mode==DYNAMIC"


@dataclass(frozen=True)
class EndpointOutByRegexFilterAction(FilterAction):
    type: str = "Endpoint filtered out by regexp"


@dataclass(frozen=True)
class TagFilteredOutFilterAction(FilterAction):
    type: str = "Tag filtered out"


@dataclass(frozen=True)
class EndpointOutByTagFilterAction(FilterAction):
    type: str = "Endpoint filtered out by tag"


@dataclass(frozen=True)
class BasePathEndpointConflictFilterWarning(FilterWarning):
    type: str = "New basePath incompatible with endpoint path"


@dataclass(frozen=True)
class EndpointOutByBasePathFilterAction(FilterAction):
    type: str = "Endpoint filtered out as incompatible with new basePath"


@dataclass(frozen=True)
class EndpointPathNormalisedFilterAction(FilterAction):
    old_path: str
    new_path: str
    type: str = "Endpoint normalised for new basePath"


@dataclass(frozen=True)
class BasePathRewrittenFilterAction(FilterAction):
    old_base_path: str
    new_base_path: str
    type: str = "basePath rewritten"


@dataclass(frozen=True)
class ParameterDefinitionValidationError(ValidationError):
    """An error on a parameter definition"""

    parameter_name: str
    type: str = "Parameter definition error"


@dataclass(frozen=True)
class ReferenceNotFoundValidationError(ValidationError):
    """An error on a reference used but not found"""

    type: str = "Reference not found"


@dataclass(frozen=True)
class ReferenceInvalidSyntax(ValidationError):
    """An error on a reference that has not a valid syntax"""

    type: str = "Reference invalid syntax"


@dataclass(frozen=True)
class ReferenceInvalidSection(ValidationError):
    """An error on a reference that refers to a invalid section"""

    type: str = "Reference invalid section"


@dataclass(frozen=True)
class SecurityDefinitionNotFoundValidationError(ValidationError):
    """An error on a securityDefinition used but not found"""

    type: str = "Security definition not found"


@dataclass(frozen=True)
class OAuth2ScopeNotFoundInSecurityDefinitionValidationError(ValidationError):
    """An error on an OAuth2 scope used but not found"""

    type: str = "Security scope not found"


@dataclass(frozen=True)
class DuplicateOperationIdValidationError(ValidationError):
    """An error on two operations using the same operationId
    """

    #: the name of the duplicate operationId
    operationId: str
    #: the path of the first operation using the operationId
    path_already_used: Iterable[Union[str, Iterable[str]]]
    type: str = "Duplicate operationId"


@dataclass(frozen=True)
class JsonSchemaValidationError(ValidationError):
    """An error due to an invalid schema"""

    type: str = "Json schema validator error"


@dataclass(frozen=True)
class BasePathValidationAction(ValidationAction):
    old_path: str
    new_path: str
