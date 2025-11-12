from __future__ import annotations

from pydantic import BaseModel, Field


class BookingPreferences(BaseModel):
    """
    Captures the follow-up information that might be collected via ctx.elicit().
    """

    checkAlternative: bool = Field(
        default=True,
        description=(
            "Set to false when the guest does not want to provide alternative "
            "options and prefers to cancel the booking attempt."
        ),
    )
    alternativeDate: str | None = Field(
        default=None,
        description="Optional alternative check-in date in ISO format (YYYY-MM-DD).",
    )
    alternativeRoom: str | None = Field(
        default=None,
        description="Optional alternative room type such as standard, deluxe, or suite.",
    )
