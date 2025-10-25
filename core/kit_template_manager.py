from pathlib import Path
from core.settings_manager import load_settings

# Module-level cache: display name -> full .bat path
_TEMPLATE_MAP = {}

def _templates_dir() -> Path:
    """
    Return the folder that actually contains the isaac-sim*.bat launchers:
    <ISAAC_SIM_PATH>\_build\windows-x86_64\release
    """
    isaac_root = Path(load_settings().get("isaac_sim_path", r"C:\Users\bruni\isaacsim"))
    return isaac_root / "_build" / "windows-x86_64" / "release"

def _stem_to_display(stem: str) -> str:
    """
    Convert a file stem like:
      'isaac-sim'                        -> 'Default'
      'isaac-sim.streaming'              -> 'Streaming'
      'isaac-sim.action_and_event_data_generation' -> 'Action and Event Data Generation'
      'isaac-sim.xr.vr'                  -> 'XR VR'
    """
    if stem == "isaac-sim":
        return "Default"
    suffix = stem.split("isaac-sim.", 1)[1]  # e.g. 'streaming' or 'xr.vr' or 'action_and_event_data_generation'

    # Make a readable label: underscores -> spaces, dots -> spaces, title case
    display = suffix.replace(".", " ").replace("_", " ").strip()
    display = " ".join(w.upper() if w.lower() in {"xr", "vr"} else w.capitalize() for w in display.split())
    return display or "Default"

def _rebuild_template_map():
    """Scan the release dir and rebuild the DISPLAY->PATH map."""
    _TEMPLATE_MAP.clear()
    d = _templates_dir()
    if not d.exists():
        return

    # Find all isaac-sim*.bat in the release dir
    for bat in d.glob("isaac-sim*.bat"):
        display = _stem_to_display(bat.stem)
        _TEMPLATE_MAP[display] = bat

    # Ensure 'Default' exists if isaac-sim.bat is present at the release dir root
    # (it will be caught by the glob above as 'isaac-sim')
    # Nothing extra to do here—just documenting the behavior.

def get_kit_templates() -> list[str]:
    """
    Return a list of display names for the template dropdown.
    Builds and caches a DISPLAY->PATH map for later resolution.
    """
    if not _TEMPLATE_MAP:
        _rebuild_template_map()

    if not _TEMPLATE_MAP:
        # Fallback if path missing or nothing found
        return ["Default"]

    # Put 'Default' first, then others alphabetically
    names = sorted(n for n in _TEMPLATE_MAP.keys() if n != "Default")
    return (["Default"] if "Default" in _TEMPLATE_MAP else []) + names

def resolve_template_bat(template_display: str) -> Path:
    """
    Given a display name from the dropdown, return the exact .bat Path.
    If the cache is empty or stale, rebuild it.
    """
    if not _TEMPLATE_MAP or template_display not in _TEMPLATE_MAP:
        _rebuild_template_map()
    if template_display not in _TEMPLATE_MAP:
        raise FileNotFoundError(f"Template '{template_display}' not found in {_templates_dir()}")
    return _TEMPLATE_MAP[template_display]
