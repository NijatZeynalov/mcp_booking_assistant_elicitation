from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "rooms.json"


class DataLoadError(RuntimeError):
    """Raised when the rooms dataset cannot be loaded."""


def load_rooms() -> Dict[str, Dict[str, int]]:

    try:
        with DATA_PATH.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except FileNotFoundError as exc:
        raise DataLoadError(
            f"Rooms dataset not found at {DATA_PATH}. "
            "Make sure data/rooms.json exists."
        ) from exc


def check_availability(date: str, room_type: str) -> bool:
    """
    Return True when at least one room of the requested type is available on the date.
    """

    rooms = load_rooms()
    normalized_type = normalize_room_type(room_type)
    day_inventory = rooms.get(date, {})
    return day_inventory.get(normalized_type, 0) > 0


def normalize_room_type(room_type: str) -> str:
    """
    Normalize the user provided room type so that lookups stay consistent.
    """

    return room_type.strip().lower()


def describe_available_options(date: str) -> str:
    """
    Provide a human-readable summary of room availability for a given date.
    """

    rooms = load_rooms()
    day_inventory = rooms.get(date)
    if not day_inventory:
        return "No inventory data for that date."

    fragments: list[str] = []
    for room_type, count in day_inventory.items():
        label = f"{room_type} ({count} left)" if count > 0 else f"{room_type} (sold out)"
        fragments.append(label)

    return ", ".join(fragments)
