from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from server.main import _book_room_impl


ElicitationHandler = Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]


@dataclass
class LocalContext:
    """
    Minimal ToolContext replacement so we can exercise the booking logic locally.
    """

    handler: ElicitationHandler

    async def elicit(self, *, message: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        return await self.handler(message, schema)


async def elicitation_callback_handler(message: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Print the elicitation prompt and gather data from the CLI user.
    """

    print("\n--- ELICITATION REQUEST ---")
    print(message)
    print(f"Schema keys: {list(schema.get('properties', {}).keys())}")

    choice = input("Proceed with alternatives? (y/n): ").strip().lower()
    if choice.startswith("n"):
        return {
            "checkAlternative": False,
            "alternativeDate": None,
            "alternativeRoom": None,
        }

    alt_date = input("Alternative date (YYYY-MM-DD, blank to keep current): ").strip() or None
    alt_room = input("Alternative room type (standard/deluxe/suite, blank to keep current): ").strip() or None
    return {
        "checkAlternative": True,
        "alternativeDate": alt_date,
        "alternativeRoom": alt_room,
    }


async def run_demo(date: str, room_type: str) -> None:
    ctx = LocalContext(handler=elicitation_callback_handler)
    result = await _book_room_impl(date=date, room_type=room_type, ctx=ctx)
    print("\nResult:", result)


if __name__ == "__main__":
    print("Hotel booking CLI demo")
    date = input("Desired date (YYYY-MM-DD): ").strip()
    room_type = input("Room type (standard/deluxe/suite): ").strip()
    asyncio.run(run_demo(date=date, room_type=room_type))
