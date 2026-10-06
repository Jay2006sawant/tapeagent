"""TapeAgent — record/replay regression testing for agent runs."""

from tapeagent.cassette import AgentRun, Cassette, Interaction, InteractionKind
from tapeagent.openai_shim import TapedOpenAI, chat_completions_create
from tapeagent.session import TapeMode, TapeSession, tape

__all__ = [
    "AgentRun",
    "Cassette",
    "Interaction",
    "InteractionKind",
    "TapeMode",
    "TapeSession",
    "TapedOpenAI",
    "chat_completions_create",
    "tape",
]

__version__ = "0.1.0"
