"""LLM client wrapper that routes through a TapeSession."""

from __future__ import annotations

from typing import Any, Callable

from tapeagent.session import TapeSession


class TapedLLM:
    """Wrap any sync LLM callable; records messages in / responses out."""

    def __init__(
        self,
        session: TapeSession,
        callable_llm: Callable[..., dict[str, Any]],
        *,
        model: str = "mock-llm",
    ) -> None:
        self.session = session
        self.callable_llm = callable_llm
        self.model = model

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        request = {"messages": messages, **kwargs}

        if self.session.is_replaying:
            response = self.session.record_llm(request, {}, model=self.model)
            return response

        response = self.callable_llm(messages, model=self.model, **kwargs)
        self.session.record_llm(request, response, model=self.model)
        return response
