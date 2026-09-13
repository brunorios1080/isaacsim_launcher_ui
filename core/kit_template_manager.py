"""Discover runnable experiences in the installed Isaac Sim package."""

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class Template:
    key: str
    title: str
    description: str
    kind: str = "sim"
    requires_headless: bool = False


EXPERIENCES = {
    "isaacsim.exp.full.kit": ("Isaac Sim · Full editor", "Create and edit scenes, robots, and sensors."),
    "isaacsim.exp.full.fabric.kit": ("Isaac Sim · Fabric", "Full editor with the Fabric experience settings."),
    "isaacsim.exp.full.newton.kit": ("Isaac Sim · Newton", "Full editor configured for the Newton physics workflow."),
    "isaacsim.exp.full.streaming.kit": ("Isaac Sim · WebRTC streaming", "Run without a local window and connect using an Isaac Sim WebRTC client."),
    "isaacsim.exp.action_and_event_data_generation.full.kit": ("Isaac Sim · Action & event data generation", "Open the installed action and event data generation workspace."),
    "isaacsim.exp.base.xr.vr.kit": ("Isaac Sim · XR / VR", "Open the XR experience. Requires compatible XR hardware and runtime."),
    "isaacsim.exp.compatibility_check.kit": ("Isaac Sim · Compatibility checker", "Inspect hardware and runtime compatibility."),
    "isaacsim.exp.uidoc.kit": ("Isaac Sim · UI examples", "Explore the installed UI documentation experience."),
}


def sim_root(settings: dict) -> Path:
    return Path(settings["conda_env_path"]) / "Lib/site-packages/isaacsim"


def get_kit_templates(settings: dict) -> list[Template]:
    apps = sim_root(settings) / "apps"
    templates = [
        Template(name, title, description, requires_headless="streaming" in name)
        for name, (title, description) in EXPERIENCES.items()
        if (apps / name).is_file()
    ]
    for path in sorted(apps.glob("*.kit")):
        if path.name in EXPERIENCES or ".base" in path.name or ".python" in path.name:
            continue
        try:
            package = tomllib.loads(path.read_text(encoding="utf-8"))["package"]
        except (KeyError, ValueError, OSError):
            continue
        if "app" in package.get("keywords", []):
            templates.append(Template(path.name, package.get("title", path.stem), package.get("description", "")))
    if (Path(settings["isaac_lab_path"]) / "source/isaaclab/isaaclab/cli/__init__.py").is_file():
        templates.append(Template(
            "lab-cartpole", "Isaac Lab · Cartpole training",
            "Train a Cartpole policy with RSL-RL and Isaac Sim PhysX. Choose a small run to verify the setup.",
            kind="lab",
        ))
    return templates
