# Isaac Launcher

Windows desktop launcher for Isaac Sim 6.1 and Isaac Lab 3.0 installations
using a Conda environment.

## Setup

Install Isaac Sim and Isaac Lab in a compatible Conda environment first. Then,
from this repository, create a separate Python 3.12 environment for the launcher:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -B main.py
```

Open Settings to select the simulator's Conda environment and Isaac Lab checkout.
The defaults target an environment named `neurointent-isaac` under Anaconda and
the checkout `C:\IsaacLab-3.0`. Create shortcuts with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install_shortcuts.ps1
```

This adds Desktop and Start menu shortcuts, plus a shortcut in `C:\IsaacLab-3.0`
when that folder exists. Use the source launcher for this version; existing
executables under `dist` are older builds.

## Usage

Double-click **Isaac Launcher** on the Desktop or in `C:\IsaacLab-3.0`.
Select a template and GPU, choose whether to run headless, and click Launch.
The launcher stays open with live output and a Stop button. Closing it during a
running session asks whether to stop that session.

## Templates

The dropdown lists installed Full Editor, Fabric, Newton, WebRTC Streaming,
Action & Event Data Generation, XR/VR, Compatibility Checker, and UI Examples
experiences. It also offers a Cartpole training preset using RSL-RL and Isaac Sim
PhysX, with controls for environment count and training iterations.

WebRTC forces headless mode and requires a separate streaming client. XR requires
compatible hardware and runtime. These are installed experience files, not custom
driving scenes. Internal base/Python experiences are excluded from the menu.

## Local configuration

- Launcher: `C:\IsaacLauncher`
- Default simulator environment: `%USERPROFILE%\anaconda3\envs\neurointent-isaac`
- Isaac Lab: `C:\IsaacLab-3.0`
- Preferences: `%LOCALAPPDATA%\NeuroIntent\IsaacLauncher\settings.json`
- Logs: `%LOCALAPPDATA%\NeuroIntent\IsaacLauncher\logs`

Settings allows changing the installation folders. Refresh discovers installed
templates and NVIDIA GPUs. GPU selection uses UUIDs; the selected GPU is exposed
as CUDA device 0 for that session, and multi-GPU rendering is disabled.

The launcher has its own small Python environment with PySide6. Simulator processes
run in the existing Conda environment with no dependency synchronization or
changes to the working scientific environment. No console window is needed for
the shortcut. Source paths are resolved independently of the current directory.

## Development

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
powershell -NoProfile -ExecutionPolicy Bypass -File .\install_shortcuts.ps1
```

## Validation

Four launcher unit tests passed. The GUI's Launch button completed a real
headless Cartpole run with 16 environments and three training iterations, then
restored the controls. Full Editor reached `app ready`, ran 180 further updates,
and exited with code 0. The automated editor check suppresses the empty test
scene's save-on-exit dialog; normal launches retain the editor's save behavior.
Other installed experiences have been discovered but not individually run.

Validation reports and screenshots were recorded locally in `logs`; they are
excluded from Git along with environments and session logs.
