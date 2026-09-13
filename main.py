"""Desktop launcher for the local Isaac Sim and Isaac Lab installation."""

import codecs
from datetime import datetime
import re
import subprocess
import sys
import traceback

from PySide6.QtCore import QProcess, QProcessEnvironment, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox,
    QVBoxLayout, QWidget,
)

from core.gpu_bridge_config import get_available_gpus
from core.isaac_launcher import build_launch
from core.kit_template_manager import get_kit_templates
from core.settings_manager import APP_ROOT, DATA_ROOT, SETTINGS_FILE, defaults, load_settings, save_settings

STYLE = """
QMainWindow, QDialog { background: #101419; color: #e9edf1; }
QWidget { color: #e9edf1; font-family: 'Segoe UI'; font-size: 14px; }
QLabel#eyebrow { color: #a7d866; font-size: 11px; font-weight: 700; letter-spacing: 2px; }
QLabel#title { font-size: 32px; font-weight: 650; }
QLabel#muted { color: #95a1ae; }
QFrame#card { background: #191f27; border: 1px solid #303946; border-radius: 12px; }
QComboBox, QLineEdit, QSpinBox { background: #11171e; border: 1px solid #3a4655; border-radius: 6px; padding: 9px 12px; min-height: 22px; selection-background-color: #324c24; }
QComboBox:hover, QLineEdit:focus, QSpinBox:focus { border-color: #94c95b; }
QComboBox::drop-down { width: 30px; border: none; }
QComboBox::down-arrow { image: url(C:/IsaacLauncher/ui/chevron.svg); width: 14px; height: 14px; }
QComboBox QAbstractItemView { background: #1e2732; color: #e9edf1; selection-background-color: #354b2a; padding: 6px; border: 1px solid #52606f; }
QPushButton { background: #252e39; border: 1px solid #3a4655; border-radius: 6px; padding: 9px 17px; min-height: 20px; }
QPushButton:hover { background: #344151; }
QPushButton#launch { background: #a7db62; color: #142009; font-weight: 700; border: none; padding: 12px 25px; }
QPushButton#launch:hover { background: #b8ea78; }
QPushButton:disabled { color: #65717e; background: #202731; border-color: #29333f; }
QCheckBox { spacing: 9px; }
QCheckBox::indicator { width: 17px; height: 17px; border-radius: 4px; border: 1px solid #536174; background: #11171e; }
QCheckBox::indicator:checked { background: #a7db62; border-color: #a7db62; image: url(C:/IsaacLauncher/ui/check.svg); }
QPlainTextEdit { background: #0b1015; color: #b9c7d6; border: 1px solid #2c3642; border-radius: 8px; padding: 9px; font-family: Consolas; font-size: 12px; }
QLabel#status { color: #bedda0; }
QToolTip { background: #263342; color: white; border: 1px solid #52606f; }
"""


class Launcher(QMainWindow):
    def __init__(self, settings_path=SETTINGS_FILE):
        super().__init__()
        self.settings_path = settings_path
        self.startup_error = ""
        try:
            self.settings = load_settings(settings_path)
        except ValueError as error:
            self.settings = defaults()
            self.startup_error = str(error)
        self.process = None
        self.log_handle = None
        self.log_path = None
        self.stopping = False
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self.setWindowTitle("Isaac Launcher")
        self.setWindowIcon(QIcon(str(APP_ROOT / "ui/icon.ico")))
        self.resize(790, 755)
        self.setMinimumSize(730, 700)
        self.setStyleSheet(STYLE.replace("C:/IsaacLauncher/ui", (APP_ROOT / "ui").as_posix()))
        body = QWidget()
        self.setCentralWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(30, 25, 30, 24)
        layout.setSpacing(13)
        eyebrow = QLabel("NEUROINTENT  /  LOCAL WORKSTATION")
        eyebrow.setObjectName("eyebrow")
        layout.addWidget(eyebrow)
        title = QLabel("Isaac Launcher")
        title.setObjectName("title")
        layout.addWidget(title)
        subtitle = QLabel("Choose a workspace. Launch on your GPU.")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("card")
        form = QVBoxLayout(card)
        form.setContentsMargins(20, 18, 20, 20)
        form.setSpacing(10)
        form.addWidget(QLabel("Launch template"))
        self.template_combo = QComboBox()
        self.template_combo.setObjectName("templateComboBox")
        form.addWidget(self.template_combo)
        self.description = QLabel()
        self.description.setObjectName("muted")
        self.description.setWordWrap(True)
        self.description.setMinimumHeight(38)
        form.addWidget(self.description)
        gpu_row = QHBoxLayout()
        gpu_row.addWidget(QLabel("GPU"))
        gpu_row.addStretch()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setToolTip("Detect newly installed GPUs and available templates")
        gpu_row.addWidget(self.refresh_button)
        form.addLayout(gpu_row)
        self.gpu_combo = QComboBox()
        self.gpu_combo.setObjectName("gpuComboBox")
        form.addWidget(self.gpu_combo)
        self.headless = QCheckBox("Headless · run without a simulation window")
        self.headless.setChecked(bool(self.settings["headless"]))
        form.addWidget(self.headless)
        self.training_options = QWidget()
        train_row = QHBoxLayout(self.training_options)
        train_row.setContentsMargins(0, 3, 0, 0)
        train_row.addWidget(QLabel("Environments"))
        self.num_envs = QSpinBox()
        self.num_envs.setRange(1, 4096)
        self.num_envs.setValue(int(self.settings["num_envs"]))
        train_row.addWidget(self.num_envs)
        train_row.addSpacing(16)
        train_row.addWidget(QLabel("Training iterations"))
        self.iterations = QSpinBox()
        self.iterations.setRange(1, 100000)
        self.iterations.setValue(int(self.settings["iterations"]))
        train_row.addWidget(self.iterations)
        form.addWidget(self.training_options)
        layout.addWidget(card)

        actions = QHBoxLayout()
        self.launch_button = QPushButton("Launch Isaac Sim")
        self.launch_button.setObjectName("launch")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.settings_button = QPushButton("Settings")
        actions.addWidget(self.launch_button)
        actions.addWidget(self.stop_button)
        actions.addStretch()
        actions.addWidget(self.settings_button)
        layout.addLayout(actions)
        self.status = QLabel("Ready")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("SESSION OUTPUT"))
        log_header.addStretch()
        open_logs = QPushButton("Open logs")
        open_logs.clicked.connect(self.open_logs)
        log_header.addWidget(open_logs)
        layout.addLayout(log_header)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(1500)
        self.output.setPlaceholderText("Launch a template to see its output here. First startup may take a few minutes.")
        layout.addWidget(self.output, 1)
        self.installation = QLabel()
        self.installation.setObjectName("muted")
        layout.addWidget(self.installation)

        self.template_combo.currentIndexChanged.connect(self.template_changed)
        self.refresh_button.clicked.connect(self.refresh_options)
        self.launch_button.clicked.connect(self.launch_sim)
        self.stop_button.clicked.connect(self.stop_sim)
        self.settings_button.clicked.connect(self.open_settings)
        self.refresh_options()
        if self.startup_error:
            self.output.setPlainText(self.startup_error + "\nDefault settings loaded; save Settings to repair the file.")

    def refresh_options(self):
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        for template in get_kit_templates(self.settings):
            self.template_combo.addItem(template.title, template)
            if template.key == self.settings.get("template"):
                self.template_combo.setCurrentIndex(self.template_combo.count() - 1)
        self.template_combo.blockSignals(False)
        self.gpu_combo.clear()
        try:
            for gpu in get_available_gpus():
                self.gpu_combo.addItem(gpu.label, gpu)
                if gpu.uuid == self.settings.get("gpu_uuid"):
                    self.gpu_combo.setCurrentIndex(self.gpu_combo.count() - 1)
            self.status.setText("Ready" if self.gpu_combo.count() else "No NVIDIA GPU detected. Check the driver, then Refresh.")
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            self.status.setText(f"GPU detection failed: {error}")
        self.installation.setText(f"Environment: {self.settings['conda_env_path'].replace(chr(92), '/').rsplit('/', 1)[-1]}    ·    {self.settings['isaac_lab_path']}")
        self.template_changed()

    def template_changed(self):
        template = self.template_combo.currentData()
        self.description.setText(template.description if template else "No templates found. Check the installation paths in Settings.")
        is_lab = template is not None and template.kind == "lab"
        self.training_options.setVisible(is_lab)
        self.launch_button.setText("Start training" if is_lab else "Launch Isaac Sim")
        self.headless.setEnabled(not (template and template.requires_headless))
        if template and template.requires_headless:
            self.headless.setChecked(True)
        self.launch_button.setEnabled(template is not None and self.gpu_combo.currentData() is not None and not self.running())

    def running(self):
        return self.process is not None and self.process.state() != QProcess.NotRunning

    def save_preferences(self):
        template, gpu = self.template_combo.currentData(), self.gpu_combo.currentData()
        self.settings.update({
            "template": template.key if template else "", "gpu_uuid": gpu.uuid if gpu else "",
            "headless": self.headless.isChecked(), "num_envs": self.num_envs.value(),
            "iterations": self.iterations.value(),
        })
        save_settings(self.settings, self.settings_path)

    def launch_sim(self):
        if self.running():
            return
        try:
            self.save_preferences()
            template, gpu = self.template_combo.currentData(), self.gpu_combo.currentData()
            spec = build_launch(self.settings, template, gpu)
            log_dir = DATA_ROOT / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            self.log_path = log_dir / (datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".log")
            self.log_handle = self.log_path.open("w", encoding="utf-8", buffering=1, newline="")
            self.output.clear()
            self.decoder = codecs.getincrementaldecoder("utf-8")("replace")
            self.append_output(f"{template.title}\n{gpu.label}\nLog: {self.log_path}\n\n")
            process = QProcess(self)
            self.process = process
            environment = QProcessEnvironment()
            for key, value in spec.environment.items():
                environment.insert(key, value)
            process.setProcessEnvironment(environment)
            process.setWorkingDirectory(spec.cwd)
            process.setProcessChannelMode(QProcess.MergedChannels)
            process.readyReadStandardOutput.connect(self.read_output)
            process.started.connect(lambda: self.status.setText(f"Running · {template.title}"))
            process.errorOccurred.connect(self.process_error)
            process.finished.connect(self.process_finished)
            self.stopping = False
            self.set_busy(True)
            self.status.setText("Starting…")
            process.start(spec.program, spec.arguments)
        except (OSError, ValueError, TypeError, AttributeError) as error:
            self.status.setText("Launch failed")
            QMessageBox.critical(self, "Unable to launch", str(error))

    def set_busy(self, busy):
        for widget in (self.template_combo, self.gpu_combo, self.refresh_button, self.settings_button, self.num_envs, self.iterations):
            widget.setEnabled(not busy)
        template = self.template_combo.currentData()
        self.headless.setEnabled(not busy and not (template and template.requires_headless))
        self.launch_button.setEnabled(not busy and template is not None and self.gpu_combo.currentData() is not None)
        self.stop_button.setEnabled(busy)

    def append_output(self, text):
        if self.log_handle:
            self.log_handle.write(text)
        clean = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text).replace("\r", "")
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(clean)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def read_output(self):
        if self.process:
            self.append_output(self.decoder.decode(bytes(self.process.readAllStandardOutput())))

    def process_error(self, error):
        if error == QProcess.FailedToStart:
            self.append_output("\nCould not start: " + self.process.errorString() + "\n")
            self.status.setText("Launch failed · see output")
            self.set_busy(False)
            self.close_log()

    def close_log(self):
        if self.log_handle:
            self.log_handle.close()
            self.log_handle = None

    def process_finished(self, code, exit_status):
        self.read_output()
        self.append_output(self.decoder.decode(b"", final=True))
        if self.stopping:
            status = "Stopped"
        elif code == 0 and exit_status == QProcess.NormalExit:
            status = "Session finished successfully"
        else:
            status = f"Session exited with code {code} · see output"
        self.append_output(f"\n{status}\n")
        self.status.setText(status)
        self.close_log()
        self.set_busy(False)

    def stop_sim(self):
        if not self.running():
            return
        self.stopping = True
        self.status.setText("Stopping…")
        process = self.process
        process.terminate()
        QTimer.singleShot(4000, lambda: process.kill() if process.state() != QProcess.NotRunning else None)

    def open_logs(self):
        folder = DATA_ROOT / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def open_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Installation settings")
        dialog.setMinimumWidth(630)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Select the existing installation folders."))
        form = QFormLayout()
        fields = {}
        for key, label in (("conda_env_path", "Conda environment"), ("isaac_lab_path", "Isaac Lab checkout")):
            row = QHBoxLayout()
            edit = QLineEdit(self.settings[key])
            button = QPushButton("Browse")
            button.clicked.connect(lambda checked=False, field=edit: self.browse_folder(field))
            row.addWidget(edit)
            row.addWidget(button)
            form.addRow(label, row)
            fields[key] = edit
        layout.addLayout(form)
        hint = QLabel("The Conda folder should contain python.exe. Preferences are saved for your Windows account.")
        hint.setWordWrap(True)
        hint.setObjectName("muted")
        layout.addWidget(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.Accepted:
            self.settings.update({key: field.text().strip() for key, field in fields.items()})
            try:
                save_settings(self.settings, self.settings_path)
                self.refresh_options()
            except (OSError, ValueError) as error:
                QMessageBox.critical(self, "Cannot save settings", str(error))

    def browse_folder(self, field):
        folder = QFileDialog.getExistingDirectory(self, "Select folder", field.text())
        if folder:
            field.setText(folder)

    def closeEvent(self, event):
        if self.running():
            answer = QMessageBox.question(self, "Simulation is running", "Stop the running session and close the launcher?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            self.stopping = True
            self.process.kill()
            self.process.waitForFinished(3000)
        try:
            self.save_preferences()
        except OSError:
            pass
        self.close_log()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = Launcher()
    window.show()
    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        (DATA_ROOT / "startup-error.log").write_text(traceback.format_exc(), encoding="utf-8")
        raise
