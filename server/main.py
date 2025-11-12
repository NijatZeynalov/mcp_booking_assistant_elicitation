from __future__ import annotations

from typing import Any, Protocol

try:
    from fastmcp import FastMCP, ToolContext  # type: ignore
except ImportError:  # pragma: no cover - enables local CLI demo without fastmcp
    FastMCP = None  # type: ignore

    class ToolContext(Protocol):  # type: ignore
        async def elicit(self, *, message: str, schema: dict[str, Any]) -> dict[str, Any]:
            ...

    class _StubMCP:
        def tool(self, *_args, **_kwargs):
            def decorator(func):
                return func

            return decorator

        def run(self) -> None:
            raise RuntimeError(
                "fastmcp is not installed. Install fastmcp to expose the MCP server."
            )

    def _build_server():
        return _StubMCP()

else:

    def _build_server():
        return FastMCP(
            "hotel-booking",
            instructions=(
                "You help users book hotel rooms by gathering a date (YYYY-MM-DD) and a "
                "room type (standard, deluxe, suite). When the requested room is sold out "
                "you should call the MCP tool again with alternative preferences gathered "
                "from the user."
            ),
        )

from server.models import BookingPreferences
from server.utils import check_availability, describe_available_options, normalize_room_type

SUCCESS_PREFIX = "[SUCCESS]"
CANCELLED_PREFIX = "[CANCELLED]"

mcp = _build_server()


def _format_success(date: str, room_type: str) -> str:
    return f"{SUCCESS_PREFIX} Booked for {date} ({room_type})"


def _format_cancelled(reason: str) -> str:
    return f"{CANCELLED_PREFIX} {reason}"


async def _elicit_preferences(ctx: ToolContext, message: str) -> BookingPreferences:
    """
    Ask the LLM/user for alternative booking instructions using ctx.elicit().
    """

    response: Any = await ctx.elicit(
        message=message,
        schema=BookingPreferences.model_json_schema(),
    )
    return BookingPreferences.model_validate(response)


async def _book_room_impl(
    date: str | None = None,
    room_type: str | None = None,
    ctx: ToolContext | None = None,
) -> str:
    """
    Main booking tool.

    - Validates the incoming payload.
    - Checks availability via server.utils.check_availability().
    - Triggers elicitation via ctx.elicit() when the request cannot be satisfied.
    """

    if ctx is None:
        raise RuntimeError("ToolContext is required for book_room.")

    if not date or not room_type:
        preferences = await _elicit_preferences(
            ctx,
            "I need both a date and a room type. "
            "Please share alternative instructions or say you would like to cancel.",
        )
        if not preferences.checkAlternative:
            return _format_cancelled("No booking made")
        date = date or preferences.alternativeDate
        room_type = room_type or preferences.alternativeRoom
        if not date or not room_type:
            return _format_cancelled("Missing required booking details")

    normalized_room_type = normalize_room_type(room_type)

    if check_availability(date, normalized_room_type):
        return _format_success(date, normalized_room_type)

    availability_summary = describe_available_options(date)
    preferences = await _elicit_preferences(
        ctx,
        (
            f"No {normalized_room_type} rooms are available on {date}. "
            f"Availability: {availability_summary}. "
            "Would you like to try another date or room type?"
        ),
    )

    if not preferences.checkAlternative:
        return _format_cancelled("No booking made")

    updated_date = preferences.alternativeDate or date
    updated_room_type = normalize_room_type(preferences.alternativeRoom or normalized_room_type)

    if not check_availability(updated_date, updated_room_type):
        return _format_cancelled(
            f"No rooms left for {updated_date} ({updated_room_type})."
        )

    return _format_success(updated_date, updated_room_type)


@mcp.tool(name="book_room", description="Book a hotel room by date and room type.")
async def book_room(
    date: str | None = None,
    room_type: str | None = None,
    ctx: ToolContext | None = None,
) -> str:
    return await _book_room_impl(date=date, room_type=room_type, ctx=ctx)


if __name__ == "__main__":
    mcp.run()
