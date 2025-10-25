from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog
from PySide6.QtUiTools import QUiLoader
import sys
import traceback

# --- Core imports ---
from core.isaac_launcher import launch_isaac_sim
from core.gpu_bridge_config import get_available_gpus, save_selected_gpu
from core.kit_template_manager import get_kit_templates
from core.settings_manager import load_settings, save_settings


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        loader = QUiLoader()

        # --- Load main UI file ---
        self.ui = loader.load("ui/main_window.ui", self)
        self.setCentralWidget(self.ui)
        self.setWindowTitle("Isaac Sim Launcher")

        # --- Populate GPU dropdown ---
        try:
            gpus = get_available_gpus()
            self.ui.gpuComboBox.addItems(gpus)

            # Load preferred GPU from settings.json
            settings = load_settings()
            preferred_gpu = settings.get("preferred_gpu")

            if preferred_gpu and preferred_gpu in gpus:
                self.ui.gpuComboBox.setCurrentText(preferred_gpu)
            else:
                self.ui.gpuComboBox.setCurrentIndex(0)

            # Save GPU selection when changed
            self.ui.gpuComboBox.currentTextChanged.connect(self.save_gpu_selection)

        except Exception as e:
            print(f"⚠️ Warning: Could not load GPUs. Error: {e}")
            self.ui.gpuComboBox.addItem("Error Loading GPUs")

        # --- Populate Kit templates dropdown ---
        try:
            templates = get_kit_templates()
            self.ui.templateComboBox.addItems(templates)
        except Exception as e:
            print(f"⚠️ Warning: Could not load templates. Error: {e}")
            self.ui.templateComboBox.addItem("Error Loading Templates")

        # --- Connect buttons ---
        self.ui.launchButton.clicked.connect(self.launch_sim)
        if hasattr(self.ui, "settingsButton"):
            self.ui.settingsButton.clicked.connect(self.open_settings)

        # --- Disable launch if no RTX GPU ---
        current_gpu = self.ui.gpuComboBox.currentText()
        if not ("NVIDIA" in current_gpu and "RTX" in current_gpu):
            self.ui.launchButton.setEnabled(False)
            self.ui.launchButton.setToolTip("Isaac Sim requires an NVIDIA RTX GPU.")
        else:
            self.ui.launchButton.setEnabled(True)

        # --- Watch GPU dropdown for RTX validation dynamically ---
        self.ui.gpuComboBox.currentTextChanged.connect(self.update_launch_button_state)

    # ---------------------------------------------------------------
    # Save GPU preference to settings.json
    # ---------------------------------------------------------------
    def save_gpu_selection(self, gpu_name):
        save_selected_gpu(gpu_name)
        print(f"[INFO] GPU selection saved: {gpu_name}")

    # ---------------------------------------------------------------
    # Update Launch button availability based on GPU type
    # ---------------------------------------------------------------
    def update_launch_button_state(self, gpu_name):
        if "NVIDIA" in gpu_name and "RTX" in gpu_name:
            self.ui.launchButton.setEnabled(True)
            self.ui.launchButton.setToolTip("")
        else:
            self.ui.launchButton.setEnabled(False)
            self.ui.launchButton.setToolTip("Isaac Sim requires an NVIDIA RTX GPU.")

    # ---------------------------------------------------------------
    # Launch Isaac Sim (with RTX check)
    # ---------------------------------------------------------------
    def launch_sim(self):
        gpu = self.ui.gpuComboBox.currentText()
        template = self.ui.templateComboBox.currentText()

        # --- GPU safety check ---
        if not ("NVIDIA" in gpu and "RTX" in gpu):
            QMessageBox.critical(
                self,
                "GPU Error",
                "⚠️ No NVIDIA RTX GPU detected.\nIsaac Sim requires an RTX-enabled GPU to launch.\n"
                "Please ensure you have an NVIDIA RTX GPU installed.",
            )
            return

        try:
            launch_isaac_sim(gpu=gpu, template=template)
            QMessageBox.information(self, "Launch", f"Isaac Sim launched on GPU: {gpu}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Launch failed:\n{str(e)}")
            print(traceback.format_exc())

    # ---------------------------------------------------------------
    # Open Settings Dialog
    # ---------------------------------------------------------------
    def open_settings(self):
        loader = QUiLoader()
        try:
            dialog: QDialog = loader.load("ui/settings_dialog.ui", self)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load settings dialog:\n{e}")
            return

        settings = load_settings()

        # Populate fields if available in the UI
        if hasattr(dialog, "lineEditPath"):
            dialog.lineEditPath.setText(settings.get("isaac_sim_path", ""))
        if hasattr(dialog, "checkBoxLogging"):
            dialog.checkBoxLogging.setChecked(settings.get("logging_enabled", False))

        if dialog.exec() == QDialog.Accepted:
            # Save settings when OK is pressed
            settings["isaac_sim_path"] = (
                dialog.lineEditPath.text()
                if hasattr(dialog, "lineEditPath")
                else settings.get("isaac_sim_path", "")
            )
            settings["logging_enabled"] = (
                dialog.checkBoxLogging.isChecked()
                if hasattr(dialog, "checkBoxLogging")
                else settings.get("logging_enabled", False)
            )
            save_settings(settings)
            QMessageBox.information(self, "Settings", "Settings saved successfully.")


# ---------------------------------------------------------------
# Main Application Entry Point
# ---------------------------------------------------------------
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = Launcher()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print("\n--- FATAL APPLICATION STARTUP ERROR ---")
        traceback.print_exc()
        print("---------------------------------------")
        sys.exit(1)
