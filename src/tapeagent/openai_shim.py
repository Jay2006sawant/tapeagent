"""Record/replay wrapper for OpenAI-style chat completions."""

from __future__ import annotations

from typing import Any, Callable

from tapeagent.session import TapeSession


def _normalize_openai_response(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return response
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if hasattr(response, "dict"):
        return response.dict()
    return {"raw": str(response)}


def _extract_chat_payload(messages: list[Any], **kwargs: Any) -> dict[str, Any]:
    norm_messages: list[dict[str, Any]] = []
    for m in messages:
        if isinstance(m, dict):
            norm_messages.append(m)
        elif hasattr(m, "model_dump"):
            norm_messages.append(m.model_dump())
        else:
            norm_messages.append({"role": "unknown", "content": str(m)})
    return {"messages": norm_messages, **kwargs}


def chat_completions_create(
    session: TapeSession,
    create_fn: Callable[..., Any],
    *,
    model: str,
    messages: list[Any],
    **kwargs: Any,
) -> Any:
    """Call OpenAI `chat.completions.create` through a tape session."""
    request = _extract_chat_payload(messages, model=model, **kwargs)

    if session.is_replaying:
        stored = session.record_llm(request, {}, model=model)
        return _coerce_response(stored, create_fn)

    live = create_fn(model=model, messages=messages, **kwargs)
    stored = _normalize_openai_response(live)
    # Flatten common OpenAI shape for replay consumers
    flat = _flatten_openai_completion(stored)
    session.record_llm(request, flat, model=model)
    return live


def _flatten_openai_completion(stored: dict[str, Any]) -> dict[str, Any]:
    """Store a stable subset: content + tool_calls if present."""
    try:
        choice = (stored.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        return {
            "content": message.get("content") or "",
            "tool_calls": message.get("tool_calls") or [],
            "raw": stored,
        }
    except (IndexError, TypeError, KeyError):
        return {"content": "", "tool_calls": [], "raw": stored}


def _coerce_response(stored: dict[str, Any], create_fn: Callable[..., Any]) -> Any:
    """Return dict-like replay payload; callers can read .content / tool_calls."""
    if "raw" in stored and stored.get("content") is not None:
        return stored
    return stored


class TapedChatCompletions:
    """Drop-in style wrapper: `client = TapedChatCompletions(session, openai_client)`."""

    def __init__(self, session: TapeSession, client: Any) -> None:
        self.session = session
        self._client = client

    def create(self, **kwargs: Any) -> Any:
        model = kwargs.get("model", "gpt-4o-mini")
        messages = kwargs.get("messages", [])
        return chat_completions_create(
            self.session,
            self._client.chat.completions.create,
            model=model,
            messages=messages,
            **{k: v for k, v in kwargs.items() if k not in ("model", "messages")},
        )


class TapedOpenAI:
    """Minimal namespace mirror: client.chat.completions.create(...)."""

    def __init__(self, session: TapeSession, client: Any) -> None:
        self.chat = type("Chat", (), {})()
        self.chat.completions = TapedChatCompletions(session, client)
