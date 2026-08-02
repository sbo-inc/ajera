from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

from pydantic import BaseModel

from ajera.schemas.generic import GenericRequest, GenericResponse

# =============================================================================
# CLASS: Operation
# =============================================================================


@dataclass(frozen=True)
class Operation[T]:
    """
    One API call, described without performing it.

    Everything an Ajera call needs that is not transport: the typed request
    body, the API version its token must be minted at, and the function that
    turns the decoded envelope into the result. Both clients build the same
    `Operation` and differ only in how they put it on the wire, which is what
    keeps request construction and response reshaping written once.
    """

    request: GenericRequest[Any]
    api_version: int
    parse: Callable[[dict[str, Any]], T]
    exclude: set[str] | dict[str, Any] | None = field(default=None)


# =============================================================================
# FUNCTIONS: Envelope parsers
# =============================================================================
#
# `Content` arrives in a handful of recurring shapes. Each builder below
# returns the `parse` callable for one of them, so an operation names its shape
# instead of respelling the reshaping.


# -----------------------------------------------------------------------------
# FUNCTION: envelope
# -----------------------------------------------------------------------------


def envelope[T](response: type[GenericResponse[T]]) -> Callable[[dict[str, Any]], T]:
    """
    Parse a `Content` that is modelled directly, with no reshaping.

    Returns:
        Callable[[dict[str, Any]], T]: The parser for this response model.
    """

    def parse(data: dict[str, Any]) -> T:
        return response.model_validate(data).content

    return parse


# -----------------------------------------------------------------------------
# FUNCTION: flatten
# -----------------------------------------------------------------------------


def flatten[T](
    key: str, response: type[GenericResponse[T]]
) -> Callable[[dict[str, Any]], T]:
    """
    Parse a `Content` holding one named array, by lifting the array out of it.

    Validating through the response model rather than the bare array matters
    for the `List*` responses, which sort themselves in `model_post_init`.

    Returns:
        Callable[[dict[str, Any]], T]: The parser for this response model.
    """

    def parse(data: dict[str, Any]) -> T:
        data["Content"] = cast(dict, data["Content"]).pop(key, [])
        return response.model_validate(data).content

    return parse


# -----------------------------------------------------------------------------
# FUNCTION: items
# -----------------------------------------------------------------------------


def items[T: BaseModel](
    key: str, model: type[T]
) -> Callable[[dict[str, Any]], list[T]]:
    """
    Parse a named array in `Content` straight into a list of models.

    Returns:
        Callable[[dict[str, Any]], list[T]]: The parser for this array.
    """

    def parse(data: dict[str, Any]) -> list[T]:
        content: list[Any] = cast(dict, data["Content"]).pop(key, [])
        return [model.model_validate(entry) for entry in content]

    return parse


# -----------------------------------------------------------------------------
# FUNCTION: item
# -----------------------------------------------------------------------------


def item[T: BaseModel](key: str, model: type[T]) -> Callable[[dict[str, Any]], T]:
    """
    Parse a single named object in `Content` into one model.

    Returns:
        Callable[[dict[str, Any]], T]: The parser for this object.
    """

    def parse(data: dict[str, Any]) -> T:
        content: dict[str, Any] = cast(dict, data["Content"]).pop(key, {})
        return model.model_validate(content)

    return parse


# -----------------------------------------------------------------------------
# FUNCTION: raw
# -----------------------------------------------------------------------------


def raw(data: dict[str, Any]) -> dict[str, Any]:
    """
    Return the envelope unparsed.

    Used where a later request needs the wire form of an earlier response, as
    `update_project` does with the baseline bundle it echoes back.

    Returns:
        dict[str, Any]: The envelope as decoded.
    """
    return data
