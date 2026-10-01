from typing import TypeVar, Type, Any, Optional
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLM:
    """Production LLM wrapper. In tests, use FakeLLM."""

    @classmethod
    def structured(
        cls,
        schema: Type[T],
        prompt: str,
        tier: str = "fast",
        system_prompt: Optional[str] = None,
    ) -> T:
        """Call LLM with structured output constraint.
        Requires valid API key when not mocked.
        """
        raise NotImplementedError(
            "Live LLM calls require API credentials. For testing and development, use FakeLLM."
        )


class FakeLLM:
    """Mock LLM for deterministic offline testing and scenario replay."""

    def __init__(self, responses: Optional[list[Any]] = None):
        self.responses: list[Any] = list(responses) if responses is not None else []
        self.call_history: list[dict[str, Any]] = []

    def set_responses(self, responses: list[Any]) -> None:
        self.responses = list(responses)

    def add_response(self, response: Any) -> None:
        self.responses.append(response)

    def structured(
        self,
        schema: Type[T],
        prompt: str,
        tier: str = "fast",
        system_prompt: Optional[str] = None,
    ) -> T:
        self.call_history.append({
            "schema": schema,
            "prompt": prompt,
            "tier": tier,
            "system_prompt": system_prompt,
        })
        if not self.responses:
            raise ValueError(
                f"FakeLLM has no canned responses left for schema {schema.__name__}. Call history size: {len(self.call_history)}"
            )
        resp = self.responses.pop(0)
        if isinstance(resp, schema):
            return resp
        if isinstance(resp, dict):
            return schema.model_validate(resp)
        if isinstance(resp, str):
            return schema.model_validate_json(resp)
        raise TypeError(
            f"Expected canned response of type {schema.__name__} or dict, got {type(resp)}"
        )
