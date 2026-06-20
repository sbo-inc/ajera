import json
from collections.abc import Sequence

import click
from pydantic import BaseModel

type Renderable = BaseModel | Sequence[BaseModel] | str | None

# =============================================================================
# FUNCTION: render
# =============================================================================


def render(value: Renderable) -> None:
    """
    Print a value to stdout.

    Strings are echoed verbatim; Pydantic models (or sequences of them) are
    serialized as indented JSON.
    """
    if value is None:
        return
    if isinstance(value, str):
        click.echo(value)
        return
    if isinstance(value, BaseModel):
        payload: object = value.model_dump(mode="json")
    else:
        payload = [item.model_dump(mode="json") for item in value]
    click.echo(json.dumps(payload, indent=2, default=str))
