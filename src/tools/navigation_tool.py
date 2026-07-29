import json

from langchain_core.tools import tool

from config import MAPS_JSON_PATH, PUBLIC_API_BASE_URL

# Small, static file — load once at import time rather than re-reading on every call.
with open(MAPS_JSON_PATH, encoding="utf-8") as f:
    _OFFICE_MAP_DATA: dict[str, dict[str, str]] = json.load(f)

_AVAILABLE = ", ".join(_OFFICE_MAP_DATA.keys())


@tool
def get_office_directions(destination: str) -> str:
    """
    Get walking directions to a department or facility in the office (e.g.
    "hr", "finance", "tech", "kitchen", "toilets", "eclatic", "it",
    "business_dev", "hr_marq", "hr_operations", "l_and_d", "gates").

    Returns a route description and a link to a floor map image with that
    section highlighted, starting from the face ID gates at the entrance.
    The image is shown to the user automatically — describe the route in
    your own words, don't repeat the raw JSON or the url back to them.

    Args:
        destination: The department or facility name the intern wants to reach.
    """
    key = destination.strip().lower().replace(" ", "_")

    entry = _OFFICE_MAP_DATA.get(key)
    if entry is None:
        return f"I don't have directions for '{destination}'. Available locations: {_AVAILABLE}"

    return json.dumps(
        {
            "type": "floor_map",
            "destination": key,
            "url": f"{PUBLIC_API_BASE_URL}/floor-map?highlight={key}",
            "route": entry["route"],
        }
    )
