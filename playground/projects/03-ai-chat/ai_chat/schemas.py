"""HTTP request and response schemas."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """One user turn."""

    session_id: str | None = Field(default=None, min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=20_000)


class ChatResponse(BaseModel):
    """Completed assistant turn."""

    session_id: str
    reply: str
    model: str
