"""Build shell-free launch commands for the dedicated Conda environment."""

from dataclasses import dataclass
import os
from pathlib import Path

from core.gpu_bridge_config import GPU
from core.kit_template_manager import Template, sim_root
from core.settings_manager import APP_ROOT


@dataclass(frozen=True)
class LaunchSpec:
    program: str
    arguments: list[str]
    cwd: str
    environment: dict[str, str]


def build_launch(settings: dict, template: Template, gpu: GPU) -> LaunchSpec:
    prefix = Path(settings["conda_env_path"]).resolve()
    python = prefix / "python.exe"
    lab = Path(settings["isaac_lab_path"]).resolve()
    if not python.is_file():
        raise FileNotFoundError(f"Conda Python not found: {python}")
    if not sim_root(settings).is_dir():
        raise FileNotFoundError("Isaac Sim is not installed in the selected Conda environment.")
    environment = dict(os.environ)
    for name in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "QT_QPA_PLATFORM"):
        environment.pop(name, None)
    environment.update({
        "CONDA_PREFIX": str(prefix), "CONDA_DEFAULT_ENV": prefix.name,
        "UV_PROJECT_ENVIRONMENT": str(prefix), "UV_PYTHON_PREFERENCE": "only-system",
        "OMNI_KIT_ACCEPT_EULA": "YES", "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8",
        "CUDA_VISIBLE_DEVICES": gpu.uuid,
        "PATH": os.pathsep.join([str(prefix), str(prefix / "Scripts"), str(prefix / "Library/bin"), environment.get("PATH", "")]),
    })
    gpu_flags = ["--/renderer/multiGpu/enabled=false", "--/renderer/multiGpu/activeCudaGpus=0,", "--/physics/cudaDevice=0"]
    arguments = ["-u", str(APP_ROOT / "core/run_isaac.py"), template.kind]
    headless = bool(settings["headless"]) or template.requires_headless
    if template.kind == "sim":
        if not (sim_root(settings) / "apps" / template.key).is_file():
            raise FileNotFoundError(f"Installed template is missing: {template.key}")
        arguments += [template.key, *gpu_flags]
        if headless:
            arguments.append("--no-window")
        cwd = sim_root(settings)
    else:
        if not (lab / "isaaclab.bat").is_file():
            raise FileNotFoundError(f"Isaac Lab checkout not found: {lab}")
        count, iterations = int(settings["num_envs"]), int(settings["iterations"])
        if not 1 <= count <= 4096 or not 1 <= iterations <= 100000:
            raise ValueError("Environment count or iteration count is outside the supported range.")
        arguments += [
            "train", "--rl_library", "rsl_rl", "--task", "Isaac-Cartpole-Direct",
            "--num_envs", str(count), "--max_iterations", str(iterations),
            "--device", "cuda:0", "--logger", "tensorboard", "--run_name", "launcher",
            "physics=isaacsim_physx", "--kit_args=" + " ".join(gpu_flags),
        ]
        if not headless:
            arguments += ["--visualizer", "kit"]
        cwd = lab
    return LaunchSpec(str(python), arguments, str(cwd), environment)
