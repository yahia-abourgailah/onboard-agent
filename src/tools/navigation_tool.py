import json

from langchain_core.tools import tool

from config import MAPS_JSON_PATH, PUBLIC_API_BASE_URL

# The tool returns JSON rather than prose so the API can hand the frontend a
# renderable map. These constants and the parser below keep the producer and
# every consumer of that payload agreeing on one shape.
NAVIGATION_TOOL_NAME = "get_office_directions"
FLOOR_MAP_TYPE = "floor_map"


def parse_floor_map(content: str) -> dict[str, object] | None:
    """Parse a get_office_directions result back into its floor-map payload.

    Returns None for anything that isn't one — the tool also returns a plain
    "I don't have directions for X" string when the destination is unknown.
    """
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return None
    if isinstance(data, dict) and data.get("type") == FLOOR_MAP_TYPE:
        return data
    return None


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

    The app displays that image to the user by itself. Retell the route in
    your own words and nothing else — do not copy the JSON, the url, or a
    markdown image like ![Floor Map](...) into your reply.

    Args:
        destination: The department or facility name the intern wants to reach.
    """
    key = destination.strip().lower().replace(" ", "_")

    entry = _OFFICE_MAP_DATA.get(key)
    if entry is None:
        return f"I don't have directions for '{destination}'. Available locations: {_AVAILABLE}"

    return json.dumps(
        {
            "type": FLOOR_MAP_TYPE,
            "destination": key,
            "url": f"{PUBLIC_API_BASE_URL}/floor-map?highlight={key}",
            "route": entry["route"],
        }
    )
