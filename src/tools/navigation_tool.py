import json

from langchain_core.tools import tool

from config import MAPS_JSON_PATH

# Small, static file — load once at import time rather than re-reading on every call.
with open(MAPS_JSON_PATH, encoding="utf-8") as f:
    _OFFICE_MAP_DATA: dict[str, dict[str, str]] = json.load(f)


@tool
def get_office_directions(destination: str) -> str:
    """
    Get walking directions and an ASCII floor map to a department or facility
    in the office (e.g. "hr", "finance", "tech", "kitchen", "toilets",
    "eclatic", "it", "business_dev", "hr_marq", "hr_operations", "l_and_d",
    "gates").

    Use this when an intern asks how to get somewhere physically in the
    building, starting from the face ID gates at the entrance.

    Args:
        destination: The department or facility name the intern wants to reach.
    """
    key = destination.strip().lower().replace(" ", "_")

    entry = _OFFICE_MAP_DATA.get(key)
    if entry is None:
        available = ", ".join(_OFFICE_MAP_DATA.keys())
        return f"I don't have directions for '{destination}'. Available locations: {available}"

    return f"{entry['route']}\n\n{entry['map']}"
