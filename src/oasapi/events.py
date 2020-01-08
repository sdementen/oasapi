from typing import Iterable, Union, Dict

from attr import dataclass


@dataclass(frozen=True)
class Event:
    path: Iterable[Union[str, Iterable[str]]]
    reason: str


@dataclass(frozen=True)
class Action(Event):
    type: str


@dataclass(frozen=True)
class Error(Event):
    type: str


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
class TagNotUsedFilterAction(FilterAction):
    type: str = "Tag filtered out"


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
    type: str = "Parameter definition error"


@dataclass(frozen=True)
class ReferenceNotFoundValidationError(ValidationError):
    type: str = "Reference not found"


@dataclass(frozen=True)
class SecurityDefinitionNotFoundValidationError(ValidationError):
    type: str = "Security definition not found"


@dataclass(frozen=True)
class OAuth2ScopeNotFoundInSecurityDefinitionValidationError(ValidationError):
    type: str = "Security scope not found"


@dataclass(frozen=True)
class DuplicateOperationIdValidationError(ValidationError):
    operationId: str
    type: str = "Duplicate operationId"


@dataclass(frozen=True)
class JsonSchemaValidationError(ValidationError):
    type: str = "Json schema validator error"



@dataclass(frozen=True)
class BasePathValidationAction(ValidationAction):
    old_path: str
    new_path: str
