import subprocess
import os
from pathlib import Path
from core.settings_manager import load_settings
from core.kit_template_manager import resolve_template_bat

def launch_isaac_sim(gpu: str = "default", template: str = "Default"):
    """
    Launch Isaac Sim using the selected template (display name).
    - Reads isaac_sim_path & logging_enabled from settings.json
    - Resolves the exact .bat in: <ISAAC_SIM_PATH>\_build\windows-x86_64\release
    - Non-blocking, detached launch on Windows
    """
    settings = load_settings()
    isaac_root = Path(settings.get("isaac_sim_path", r"C:\Users\bruni\isaacsim"))
    logging_enabled = settings.get("logging_enabled", False)

    if not isaac_root.exists():
        raise FileNotFoundError(f"Isaac Sim path not found: {isaac_root}")

    # Resolve the exact .bat path for the chosen template
    exe_path = resolve_template_bat(template)  # e.g. ...\release\isaac-sim.streaming.bat
    if not exe_path.exists():
        raise FileNotFoundError(f"Template launcher not found: {exe_path}")

    # Build command line
    cmd = [str(exe_path)]
    if gpu and gpu != "default":
        cmd.append(f"--gpu={gpu}")

    # Launch detached/no window
    kwargs = {
        "cwd": str(exe_path.parent),  # the release folder
        "creationflags": subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
    }

    # Optional logging
    if logging_enabled:
        log_path = Path("isaac_launcher.log")
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"\n[Launch] {cmd}\n")
            subprocess.Popen(cmd, stdout=log, stderr=log, **kwargs)
            log.write("[Status] Isaac Sim launched successfully\n")
    else:
        subprocess.Popen(cmd, **kwargs)

    print(f"✅ Launched: {exe_path.name}  (GPU: {gpu})")
