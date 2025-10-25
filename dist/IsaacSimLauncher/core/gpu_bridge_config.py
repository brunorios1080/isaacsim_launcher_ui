import subprocess
from core.settings_manager import load_settings, save_settings


def get_available_gpus():
    """
    Detect available NVIDIA GPUs on Windows using nvidia-smi.
    Falls back to simple placeholders if nvidia-smi is not found.
    """
    gpus = []

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
        )

        if result.returncode == 0 and result.stdout.strip():
            gpus = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        else:
            gpus = ["No NVIDIA GPU Found", "Integrated Graphics", "Software Renderer"]

    except FileNotFoundError:
        gpus = ["No NVIDIA GPU Found", "Integrated Graphics", "Software Renderer"]
    except Exception as e:
        print(f"⚠️ GPU detection failed: {e}")
        gpus = ["GPU Detection Error"]

    settings = load_settings()
    preferred = settings.get("preferred_gpu")

    if preferred and preferred in gpus:
        gpus.remove(preferred)
        gpus.insert(0, preferred)

    return gpus


def save_selected_gpu(gpu_name: str):
    """
    Save the selected GPU into settings.json so it persists between launches.
    """
    settings = load_settings()
    settings["preferred_gpu"] = gpu_name
    save_settings(settings)
