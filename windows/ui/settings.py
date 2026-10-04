from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = QSettings(
            "The Fat Pirate",
            "System Status"
        )

        self.setWindowTitle("Configure System Status")
        self.resize(500, 520)

        root = QVBoxLayout(self)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self.build_sensors_tab()
        self.build_appearance_tab()
        self.build_thresholds_tab()
        self.build_network_tab()
        self.build_behavior_tab()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept_changes)
        buttons.rejected.connect(self.reject)

        apply_button = buttons.button(
            QDialogButtonBox.StandardButton.Apply
        )
        apply_button.clicked.connect(self.apply)

        root.addWidget(buttons)

        self.load()

    def build_sensors_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        group = QGroupBox("Visible Sensors")
        form = QVBoxLayout(group)

        self.show_cpu = QCheckBox("CPU")
        self.show_ram = QCheckBox("RAM")
        self.show_gpu = QCheckBox("GPU")
        self.show_storage = QCheckBox("Storage")
        self.show_network = QCheckBox("Network")

        for item in (
            self.show_cpu,
            self.show_ram,
            self.show_gpu,
            self.show_storage,
            self.show_network,
        ):
            form.addWidget(item)

        layout.addWidget(group)

        storage_group = QGroupBox("Storage")
        storage_form = QFormLayout(storage_group)

        self.storage_mode = QComboBox()
        self.storage_mode.addItem(
            "All Drives", "all"
        )
        self.storage_mode.addItem(
            "Combined", "combined"
        )

        storage_form.addRow(
            "Display mode:",
            self.storage_mode
        )

        layout.addWidget(storage_group)
        layout.addStretch()

        self.tabs.addTab(page, "Sensors")

    def build_appearance_tab(self):
        page = QWidget()
        form = QFormLayout(page)

        self.font_size = QSpinBox()
        self.font_size.setRange(7, 24)
        self.font_size.setSuffix(" pt")

        self.widget_width = QSpinBox()
        self.widget_width.setRange(270, 1000)
        self.widget_width.setSuffix(" px")

        self.show_divider = QCheckBox()

        self.temperature_unit = QComboBox()
        self.temperature_unit.addItem("Celsius", "C")
        self.temperature_unit.addItem("Fahrenheit", "F")

        self.show_cpu_temperature = QCheckBox()
        self.show_gpu_temperature = QCheckBox()

        form.addRow("Font size:", self.font_size)
        form.addRow("Widget width:", self.widget_width)
        form.addRow("Show divider:", self.show_divider)
        form.addRow("Temperature unit:", self.temperature_unit)
        form.addRow("Show CPU temperature:", self.show_cpu_temperature)
        form.addRow("Show GPU temperature:", self.show_gpu_temperature)

        self.tabs.addTab(page, "Appearance")

    def build_thresholds_tab(self):
        page = QWidget()
        form = QFormLayout(page)

        self.warning_usage = QSpinBox()
        self.warning_usage.setRange(1, 99)
        self.warning_usage.setSuffix("%")

        self.critical_usage = QSpinBox()
        self.critical_usage.setRange(1, 100)
        self.critical_usage.setSuffix("%")

        self.warning_color = QPushButton()
        self.critical_color = QPushButton()

        self.warning_color.clicked.connect(
            lambda: self.choose_color(
                self.warning_color
            )
        )

        self.critical_color.clicked.connect(
            lambda: self.choose_color(
                self.critical_color
            )
        )

        form.addRow(
            "Usage warning:",
            self.warning_usage
        )
        form.addRow(
            "Usage critical:",
            self.critical_usage
        )
        form.addRow(
            "Warning color:",
            self.warning_color
        )
        form.addRow(
            "Critical color:",
            self.critical_color
        )

        self.tabs.addTab(page, "Thresholds")

    def build_network_tab(self):
        page = QWidget()
        form = QFormLayout(page)

        self.vpn_mode = QComboBox()
        self.vpn_mode.addItem(
            "Automatic", "auto"
        )
        self.vpn_mode.addItem(
            "Proton VPN", "proton"
        )
        self.vpn_mode.addItem(
            "Tailscale", "tailscale"
        )
        self.vpn_mode.addItem(
            "Any VPN / tunnel", "any"
        )
        self.vpn_mode.addItem(
            "Disable VPN security check", "disabled"
        )

        self.show_network_rates = QCheckBox()
        self.show_link_speed = QCheckBox()

        form.addRow(
            "VPN detection:",
            self.vpn_mode
        )
        form.addRow(
            "Show RX / TX:",
            self.show_network_rates
        )
        form.addRow(
            "Show link speed:",
            self.show_link_speed
        )

        self.tabs.addTab(page, "Network")

    def build_behavior_tab(self):
        page = QWidget()
        form = QFormLayout(page)

        self.refresh_ms = QSpinBox()
        self.refresh_ms.setRange(250, 10000)
        self.refresh_ms.setSingleStep(250)
        self.refresh_ms.setSuffix(" ms")

        self.start_with_windows = QCheckBox()
        self.start_locked = QCheckBox()

        form.addRow(
            "Refresh interval:",
            self.refresh_ms
        )
        form.addRow(
            "Start with Windows:",
            self.start_with_windows
        )
        form.addRow(
            "Start locked:",
            self.start_locked
        )

        self.tabs.addTab(page, "Behavior")

    def choose_color(self, button):
        current = QColor(
            button.property("color")
        )

        color = QColorDialog.getColor(
            current,
            self,
            "Choose Color"
        )

        if color.isValid():
            self.set_color_button(
                button,
                color.name()
            )

    def set_color_button(self, button, color):
        button.setProperty("color", color)
        button.setText(color)
        button.setStyleSheet(
            f"background-color: {color};"
        )

    def combo_set(self, combo, value):
        index = combo.findData(value)

        if index >= 0:
            combo.setCurrentIndex(index)

    def load(self):
        self.show_cpu.setChecked(
            self.settings.value(
                "show_cpu", True, type=bool
            )
        )

        self.show_ram.setChecked(
            self.settings.value(
                "show_ram", True, type=bool
            )
        )

        self.show_gpu.setChecked(
            self.settings.value(
                "show_gpu", True, type=bool
            )
        )

        self.show_storage.setChecked(
            self.settings.value(
                "show_storage", True, type=bool
            )
        )

        self.show_network.setChecked(
            self.settings.value(
                "show_network", True, type=bool
            )
        )

        self.combo_set(
            self.storage_mode,
            self.settings.value(
                "storage_mode", "all"
            )
        )

        self.font_size.setValue(
            self.settings.value(
                "font_size", 10, type=int
            )
        )

        self.widget_width.setValue(
            self.settings.value(
                "widget_width", 510, type=int
            )
        )

        self.show_divider.setChecked(
            self.settings.value(
                "show_divider", True, type=bool
            )
        )

        self.combo_set(
            self.temperature_unit,
            self.settings.value(
                "temperature_unit", "C"
            )
        )

        self.show_cpu_temperature.setChecked(
            self.settings.value(
                "show_cpu_temperature",
                True,
                type=bool
            )
        )

        self.show_gpu_temperature.setChecked(
            self.settings.value(
                "show_gpu_temperature",
                True,
                type=bool
            )
        )

        self.warning_usage.setValue(
            self.settings.value(
                "warning_usage", 75, type=int
            )
        )

        self.critical_usage.setValue(
            self.settings.value(
                "critical_usage", 90, type=int
            )
        )

        self.set_color_button(
            self.warning_color,
            self.settings.value(
                "warning_color", "#ff9d00"
            )
        )

        self.set_color_button(
            self.critical_color,
            self.settings.value(
                "critical_color", "#ff3030"
            )
        )

        self.combo_set(
            self.vpn_mode,
            self.settings.value(
                "vpn_mode", "auto"
            )
        )

        self.show_network_rates.setChecked(
            self.settings.value(
                "show_network_rates",
                False,
                type=bool
            )
        )

        self.show_link_speed.setChecked(
            self.settings.value(
                "show_link_speed",
                False,
                type=bool
            )
        )

        self.refresh_ms.setValue(
            self.settings.value(
                "refresh_ms", 500, type=int
            )
        )

        self.start_with_windows.setChecked(
            self.settings.value(
                "start_with_windows",
                False,
                type=bool
            )
        )

        self.start_locked.setChecked(
            self.settings.value(
                "start_locked",
                True,
                type=bool
            )
        )

    def apply(self):
        values = {
            "show_cpu": self.show_cpu.isChecked(),
            "show_ram": self.show_ram.isChecked(),
            "show_gpu": self.show_gpu.isChecked(),
            "show_storage": self.show_storage.isChecked(),
            "show_network": self.show_network.isChecked(),
            "storage_mode": self.storage_mode.currentData(),
            "font_size": self.font_size.value(),
            "widget_width": self.widget_width.value(),
            "show_divider": self.show_divider.isChecked(),
            "temperature_unit": self.temperature_unit.currentData(),
            "show_cpu_temperature": self.show_cpu_temperature.isChecked(),
            "show_gpu_temperature": self.show_gpu_temperature.isChecked(),
            "warning_usage": self.warning_usage.value(),
            "critical_usage": self.critical_usage.value(),
            "warning_color": self.warning_color.property("color"),
            "critical_color": self.critical_color.property("color"),
            "vpn_mode": self.vpn_mode.currentData(),
            "show_network_rates": self.show_network_rates.isChecked(),
            "show_link_speed": self.show_link_speed.isChecked(),
            "refresh_ms": self.refresh_ms.value(),
            "start_with_windows": self.start_with_windows.isChecked(),
            "start_locked": self.start_locked.isChecked(),
        }

        for key, value in values.items():
            self.settings.setValue(key, value)

        self.settings.sync()

        if self.parent():
            self.parent().reload_settings()

    def accept_changes(self):
        self.apply()
        self.accept()
