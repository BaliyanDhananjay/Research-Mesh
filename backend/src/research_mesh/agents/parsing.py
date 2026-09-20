"""Parse and validate structured JSON produced by an agent's model response."""

import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def parse_agent_response(raw: str, schema: type[T]) -> T:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"Agent response was not valid JSON: {error}") from error
    try:
        return schema.model_validate(data)
    except ValidationError as error:
        raise ValueError(f"Agent response did not match the expected schema: {error}") from error
