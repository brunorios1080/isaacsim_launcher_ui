import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core.gpu_bridge_config import parse_gpus
from core.isaac_launcher import build_launch
from core.kit_template_manager import get_kit_templates
from core.settings_manager import defaults, load_settings, save_settings


class LauncherTests(unittest.TestCase):
    def test_same_model_gpus_keep_distinct_identities(self):
        gpus = parse_gpus("0, GPU-one, NVIDIA RTX 5060, 8192\n1, GPU-two, NVIDIA RTX 5060, 8192\n")
        self.assertEqual([gpu.uuid for gpu in gpus], ["GPU-one", "GPU-two"])
        self.assertNotEqual(gpus[0].label, gpus[1].label)

    def test_missing_installation_has_no_fabricated_templates(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = {**defaults(), "conda_env_path": folder, "isaac_lab_path": folder}
            self.assertEqual(get_kit_templates(settings), [])

    def test_settings_round_trip_and_corrupt_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prefs/settings.json"
            settings = {**defaults(), "template": "lab-cartpole", "headless": True}
            save_settings(settings, path)
            self.assertEqual(load_settings(path), settings)
            path.write_text("not json", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_settings(path)

    def test_launch_handles_spaces_and_isolates_selected_gpu(self):
        with tempfile.TemporaryDirectory(prefix="isaac launch ") as folder:
            root = Path(folder)
            (root / "python.exe").touch()
            apps = root / "Lib/site-packages/isaacsim/apps"
            apps.mkdir(parents=True)
            (apps / "isaacsim.exp.full.kit").touch()
            settings = {**defaults(), "conda_env_path": str(root), "headless": True}
            template = get_kit_templates(settings)[0]
            gpu = parse_gpus("1, GPU-two, NVIDIA RTX 5060, 8192\n")[0]
            with patch.dict(os.environ, {"PYTHONPATH": "old-install", "QT_PLUGIN_PATH": "launcher-qt", "CUDA_VISIBLE_DEVICES": "GPU-old"}):
                spec = build_launch(settings, template, gpu)
            self.assertEqual(spec.program, str(root / "python.exe"))
            self.assertEqual(spec.environment["CUDA_VISIBLE_DEVICES"], "GPU-two")
            self.assertNotIn("PYTHONPATH", spec.environment)
            self.assertNotIn("QT_PLUGIN_PATH", spec.environment)
            self.assertIn("--no-window", spec.arguments)
            self.assertIn("--/renderer/multiGpu/activeCudaGpus=0,", spec.arguments)
            self.assertEqual(spec.arguments[2], "sim")


if __name__ == "__main__":
    unittest.main()
