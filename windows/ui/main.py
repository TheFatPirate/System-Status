import sys
import time
from pathlib import Path

from PySide6.QtCore import (
    QPoint,
    QSettings,
    QTimer,
    Qt,
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QLabel,
    QMainWindow,
    QMenu,
    QWidget,
)

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from live import collect_live
from gpu import collect_gpu_usage
from temperature import collect_temperatures, convert_temperature
from settings import SettingsDialog


WHITE = "#ffffff"
WARNING = "#ff9d00"
CRITICAL = "#ff3030"
SECURE = "#39ff14"

WARNING_USAGE = 75.0
CRITICAL_USAGE = 90.0


class SensorRow:
    def __init__(self, parent, label, y):
        self.label = QLabel(label, parent)
        self.value = QLabel("--", parent)
        self.extra = QLabel("", parent)

        self.label.setGeometry(0, y, 78, 22)
        self.value.setGeometry(78, y, 62, 22)
        self.extra.setGeometry(150, y, 360, 22)

        self.value.setAlignment(
            Qt.AlignmentFlag.AlignRight |
            Qt.AlignmentFlag.AlignVCenter
        )

        font = QFont("Segoe UI", 10)
        font.setBold(True)

        for widget in (self.label, self.value, self.extra):
            widget.setFont(font)
            widget.setStyleSheet(
                "color: white; background: transparent;"
            )

        self.widgets = (
            self.label,
            self.value,
            self.extra,
        )

        self.state = "normal"
        self.pulse_on = False

    def set_geometry(self, y):
        self.label.move(0, y)
        self.value.move(78, y)
        self.extra.move(150, y)

    def set_text(self, value, extra=""):
        self.value.setText(value)
        self.extra.setText(extra)

    def set_state(self, state):
        self.state = state

        if state == "critical":
            color = CRITICAL
        elif state == "warning":
            color = WARNING
        else:
            color = WHITE

        for widget in self.widgets:
            widget.setStyleSheet(
                f"color: {color}; background: transparent;"
            )

            if state == "normal":
                widget.setGraphicsEffect(None)

    def pulse(self):
        if self.state == "normal":
            return

        self.pulse_on = not self.pulse_on

        color = (
            QColor(CRITICAL)
            if self.state == "critical"
            else QColor(WARNING)
        )

        for widget in self.widgets:
            if not self.pulse_on:
                widget.setGraphicsEffect(None)
                continue

            glow = QGraphicsDropShadowEffect(widget)
            glow.setOffset(0, 0)

            if self.state == "critical":
                glow.setBlurRadius(22)
            else:
                glow.setBlurRadius(14)

            glow.setColor(color)
            widget.setGraphicsEffect(glow)


class SystemStatusWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings(
            "The Fat Pirate",
            "System Status"
        )

        self.locked = self.settings.value(
            "locked",
            True,
            type=bool
        )

        self.storage_mode = self.settings.value(
            "storage_mode",
            "all"
        )

        self._drag_position = None

        self.setWindowTitle("System Status")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnBottomHint
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True
        )

        self.root = QWidget()
        self.root.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True
        )

        # Keep the entire transparent widget surface interactive.
        # Child telemetry labels ignore mouse input so right-clicks
        # and dragging are handled by the main window everywhere.
        self.root.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )

        self.setCentralWidget(self.root)

        self.rows = {}

        self.rows["cpu"] = SensorRow(
            self.root, "CPU", 0
        )
        self.rows["ram"] = SensorRow(
            self.root, "RAM", 22
        )
        self.rows["gpu"] = SensorRow(
            self.root, "GPU", 44
        )

        self.storage_rows = []

        self.divider = QWidget(self.root)
        self.divider.setStyleSheet(
            "background: rgba(255,255,255,217);"
        )

        self.system_label = QLabel(
            "SYSTEM // NETWORK:",
            self.root
        )

        self.network_label = QLabel(
            "",
            self.root
        )

        self.download_label = QLabel(
            "",
            self.root
        )

        self.upload_label = QLabel(
            "",
            self.root
        )

        footer_font = QFont("Segoe UI", 10)
        footer_font.setBold(True)

        self.system_label.setFont(footer_font)
        self.network_label.setFont(footer_font)
        self.download_label.setFont(footer_font)
        self.upload_label.setFont(footer_font)

        self.system_label.setStyleSheet(
            "color: white; background: transparent;"
        )

        self.network_label.setStyleSheet(
            "color: #28d7d7; background: transparent;"
        )

        self.download_label.setStyleSheet(
            "color: #39ff14; background: transparent;"
        )

        self.upload_label.setStyleSheet(
            "color: #39ff14; background: transparent;"
        )

        saved = self.settings.value("position")

        # Network sampling state must exist before the first refresh.
        self._network_previous = {}
        self._network_sample_time = None
        self._network_rate_history = []

        # Load settings before building the dynamic layout.
        self.reload_settings()

        if isinstance(saved, QPoint):
            self.move(saved)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(
                screen.right() - self.width() - 20,
                screen.top() + 20
            )

        self.reload_settings()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(self.refresh_ms)

        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.pulse_warnings)
        self.pulse_timer.start(550)

        self._network_previous = {}
        self._network_sample_time = None
        self._network_rate_history = []

        self.refresh()

    def reload_settings(self):
        self.storage_mode = self.settings.value(
            "storage_mode", "all"
        )

        self.warning_usage = self.settings.value(
            "warning_usage", 75, type=int
        )

        self.critical_usage = self.settings.value(
            "critical_usage", 90, type=int
        )

        self.warning_color = self.settings.value(
            "warning_color", "#ff9d00"
        )

        self.critical_color = self.settings.value(
            "critical_color", "#ff3030"
        )

        self.temperature_unit = self.settings.value(
            "temperature_unit", "C"
        )

        self.show_cpu_temperature = self.settings.value(
            "show_cpu_temperature", True, type=bool
        )

        self.show_gpu_temperature = self.settings.value(
            "show_gpu_temperature", True, type=bool
        )

        self.refresh_ms = self.settings.value(
            "refresh_ms", 500, type=int
        )

        self.widget_width = self.settings.value(
            "widget_width", 510, type=int
        )

        self.font_size = self.settings.value(
            "font_size", 10, type=int
        )

        self.show_cpu = self.settings.value(
            "show_cpu", True, type=bool
        )

        self.show_ram = self.settings.value(
            "show_ram", True, type=bool
        )

        self.show_gpu = self.settings.value(
            "show_gpu", True, type=bool
        )

        self.show_storage = self.settings.value(
            "show_storage", True, type=bool
        )

        self.show_network = self.settings.value(
            "show_network", True, type=bool
        )

        self.show_divider = self.settings.value(
            "show_divider", True, type=bool
        )

        self.vpn_mode = self.settings.value(
            "vpn_mode", "auto"
        )

        # Apply visibility settings immediately.
        self.rows["cpu"].label.setVisible(self.show_cpu)
        self.rows["cpu"].value.setVisible(self.show_cpu)
        self.rows["cpu"].extra.setVisible(self.show_cpu)

        self.rows["ram"].label.setVisible(self.show_ram)
        self.rows["ram"].value.setVisible(self.show_ram)
        self.rows["ram"].extra.setVisible(self.show_ram)

        self.rows["gpu"].label.setVisible(self.show_gpu)
        self.rows["gpu"].value.setVisible(self.show_gpu)
        self.rows["gpu"].extra.setVisible(self.show_gpu)

        self.divider.setVisible(self.show_divider)

        self.system_label.setVisible(self.show_network)
        self.network_label.setVisible(self.show_network)
        self.download_label.setVisible(self.show_network)
        self.upload_label.setVisible(self.show_network)

        # Apply font size immediately.
        for row in self.rows.values():
            font = row.label.font()
            font.setPointSize(self.font_size)
            row.label.setFont(font)

            font = row.value.font()
            font.setPointSize(self.font_size)
            row.value.setFont(font)

            font = row.extra.font()
            font.setPointSize(self.font_size)
            row.extra.setFont(font)

        footer_font = self.system_label.font()
        footer_font.setPointSize(self.font_size)

        self.system_label.setFont(footer_font)
        self.network_label.setFont(footer_font)
        self.download_label.setFont(footer_font)
        self.upload_label.setFont(footer_font)

        if hasattr(self, "refresh_timer"):
            self.refresh_timer.setInterval(
                self.refresh_ms
            )

        self.rebuild_storage_rows({})
        self.reflow_layout()
        self.refresh()

    def usage_state(self, value):
        if value >= self.critical_usage:
            return "critical"

        if value >= self.warning_usage:
            return "warning"

        return "normal"

    def update_row(self, row, value, extra=""):
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = 0.0

        row.set_text(
            f"{value:.1f}%",
            extra
        )

        row.set_state(
            self.usage_state(value)
        )

    def clear_storage_rows(self):
        for row in self.storage_rows:
            row.label.deleteLater()
            row.value.deleteLater()
            row.extra.deleteLater()

        self.storage_rows = []

    def reflow_layout(self):
        y = 0

        primary_rows = (
            ("cpu", self.show_cpu),
            ("ram", self.show_ram),
            ("gpu", self.show_gpu),
        )

        for name, visible in primary_rows:
            row = self.rows[name]

            row.label.setVisible(visible)
            row.value.setVisible(visible)
            row.extra.setVisible(visible)

            if visible:
                row.label.move(0, y)
                row.value.move(100, y)
                row.extra.move(190, y)
                y += 22

        for row in self.storage_rows:
            row.label.setVisible(self.show_storage)
            row.value.setVisible(self.show_storage)
            row.extra.setVisible(self.show_storage)

            if self.show_storage:
                row.label.move(0, y)
                row.value.move(100, y)
                row.extra.move(190, y)
                y += 22

        footer_visible = self.show_network

        self.divider.setVisible(
            self.show_divider and footer_visible
        )

        self.system_label.setVisible(footer_visible)
        self.network_label.setVisible(footer_visible)
        self.download_label.setVisible(footer_visible)
        self.upload_label.setVisible(footer_visible)

        if footer_visible:
            self.divider.setGeometry(
                0,
                y + 1,
                self.widget_width,
                1
            )

            self.system_label.setGeometry(
                0,
                y + 6,
                165,
                22
            )

            self.network_label.setGeometry(
                170,
                y + 6,
                75,
                22
            )

            self.download_label.setGeometry(
                245,
                y + 6,
                135,
                22
            )

            self.upload_label.setGeometry(
                380,
                y + 6,
                max(1, self.widget_width - 380),
                22
            )

            height = y + 32
        else:
            height = max(22, y)

        self.setFixedSize(
            self.widget_width,
            height
        )
    def rebuild_storage_rows(self, storage):
        self.clear_storage_rows()

        y = 66

        if self.storage_mode == "combined":
            row = SensorRow(
                self.root,
                "STORAGE",
                y
            )
            self.storage_rows.append(row)

        else:
            if not storage:
                row = SensorRow(
                    self.root,
                    "STORAGE",
                    y
                )
                self.storage_rows.append(row)
            else:
                first = True

                for key, drive in storage.items():
                    device = drive.get(
                        "device",
                        key.upper() + ":"
                    )

                    if first:
                        label = "STORAGE"
                        first = False
                    else:
                        label = ""

                    row = SensorRow(
                        self.root,
                        label,
                        y
                    )

                    row.extra.setText(device)

                    self.storage_rows.append(row)
                    y += 22

        self.reflow_layout()

    def update_storage(self, storage):
        wanted_rows = (
            1
            if self.storage_mode == "combined"
            else max(1, len(storage))
        )

        if len(self.storage_rows) != wanted_rows:
            self.rebuild_storage_rows(storage)

        if self.storage_mode == "combined":
            if not storage:
                self.update_row(
                    self.storage_rows[0],
                    0.0
                )
                return

            total = sum(
                d["total_bytes"]
                for d in storage.values()
            )

            used = sum(
                d["used_bytes"]
                for d in storage.values()
            )

            usage = (
                (used / total) * 100.0
                if total
                else 0.0
            )

            used_tb = used / (1024 ** 4)
            total_tb = total / (1024 ** 4)

            self.update_row(
                self.storage_rows[0],
                usage,
                f"{used_tb:.2f} / {total_tb:.2f} TB"
            )

            return

        if not storage:
            self.update_row(
                self.storage_rows[0],
                0.0,
                "NO STORAGE"
            )
            return

        for row, drive in zip(
            self.storage_rows,
            storage.values()
        ):
            device = drive["device"]

            self.update_row(
                row,
                drive["usage_percent"],
                device
            )

    def update_network(self, network):
        physical_connected = False
        tunnel_connected = False

        active_name = None
        active_data = None

        for name, data in network.items():
            if not data.get("up"):
                continue

            lower = name.lower()

            if (
                "proton" in lower
                or "vpn" in lower
                or "wireguard" in lower
            ):
                tunnel_connected = True

            if data.get("virtual", False):
                continue

            if (
                "loopback" in lower
                or "bluetooth" in lower
            ):
                continue

            if data.get("speed_mbps", 0) <= 0:
                continue

            physical_connected = True

            if active_data is None:
                active_name = name
                active_data = data

        if not physical_connected:
            state = "OFFLINE"
            color = CRITICAL
        elif tunnel_connected:
            state = "SECURE"
            color = SECURE
        else:
            state = "ONLINE"
            color = WHITE

        download_rate = 0.0
        upload_rate = 0.0

        now = time.monotonic()

        if active_name is not None:
            received = active_data.get(
                "bytes_received", 0
            )
            sent = active_data.get(
                "bytes_sent", 0
            )

            previous = self._network_previous.get(
                active_name
            )

            if (
                previous is not None
                and self._network_sample_time is not None
            ):
                elapsed = (
                    now - self._network_sample_time
                )

                if elapsed > 0:
                    download_rate = max(
                        0,
                        received - previous[0]
                    ) / elapsed

                    upload_rate = max(
                        0,
                        sent - previous[1]
                    ) / elapsed

            self._network_previous = {
                active_name: (received, sent)
            }

        self._network_sample_time = now

        # Keep a rolling three-second throughput history.
        self._network_rate_history.append(
            (now, download_rate, upload_rate)
        )

        cutoff = now - 3.0

        self._network_rate_history = [
            sample
            for sample in self._network_rate_history
            if sample[0] >= cutoff
        ]

        if self._network_rate_history:
            download_rate = sum(
                sample[1]
                for sample in self._network_rate_history
            ) / len(self._network_rate_history)

            upload_rate = sum(
                sample[2]
                for sample in self._network_rate_history
            ) / len(self._network_rate_history)

        def format_rate(value):
            if value >= 1024 ** 2:
                return (
                    f"{value / (1024 ** 2):.1f} MB/s"
                )

            if value >= 1024:
                return (
                    f"{value / 1024:.0f} KB/s"
                )

            return f"{value:.0f} B/s"

        self.network_label.setText(state)

        self.download_label.setText(
            f"↓ {format_rate(download_rate)}"
        )

        self.upload_label.setText(
            f"↑ {format_rate(upload_rate)}"
        )

        if state == "SECURE":
            status_color = "#39ff14"
        elif state == "OFFLINE":
            status_color = "#ff3030"
        else:
            status_color = "#28d7d7"

        self.network_label.setStyleSheet(
            f"color: {status_color}; "
            "background: transparent;"
        )

        self.download_label.setStyleSheet(
            "color: #39ff14; "
            "background: transparent;"
        )

        self.upload_label.setStyleSheet(
            "color: #39ff14; "
            "background: transparent;"
        )
    def refresh(self):
        live = collect_live()

        temperatures = collect_temperatures()

        cpu_extra = ""
        gpu_extra = ""

        if self.show_cpu_temperature:
            cpu_temp = convert_temperature(
                temperatures["cpu_c"],
                self.temperature_unit
            )

            if cpu_temp is not None:
                cpu_extra = (
                    f"{cpu_temp:.0f}°"
                    f"{self.temperature_unit.upper()}"
                )

        if self.show_gpu_temperature:
            gpu_temp = convert_temperature(
                temperatures["gpu_c"],
                self.temperature_unit
            )

            if gpu_temp is not None:
                gpu_extra = (
                    f"{gpu_temp:.0f}°"
                    f"{self.temperature_unit.upper()}"
                )

        self.update_row(
            self.rows["cpu"],
            live["cpu"]["usage_percent"],
            cpu_extra
        )

        self.update_row(
            self.rows["ram"],
            live["memory"]["usage_percent"]
        )

        gpu_usage = collect_gpu_usage()

        self.update_row(
            self.rows["gpu"],
            gpu_usage if gpu_usage is not None else 0.0,
            gpu_extra
        )

        storage = live.get(
            "storage",
            {}
        )

        self.update_storage(storage)

        self.update_network(
            live.get("network", {})
        )

    def pulse_warnings(self):
        for row in self.rows.values():
            row.pulse()

        for row in self.storage_rows:
            row.pulse()

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        storage_menu = menu.addMenu(
            "Storage Display"
        )

        combined_action = storage_menu.addAction(
            "Combined"
        )
        combined_action.setCheckable(True)
        combined_action.setChecked(
            self.storage_mode == "combined"
        )

        all_action = storage_menu.addAction(
            "All Drives"
        )
        all_action.setCheckable(True)
        all_action.setChecked(
            self.storage_mode == "all"
        )

        menu.addSeparator()

        configure_action = menu.addAction(
            "Configure System Status..."
        )

        menu.addSeparator()

        if self.locked:
            lock_action = menu.addAction(
                "Unlock Widget"
            )
        else:
            lock_action = menu.addAction(
                "Lock Widget"
            )

        menu.addSeparator()

        exit_action = menu.addAction(
            "Exit System Status"
        )

        selected = menu.exec(
            event.globalPos()
        )

        if selected == configure_action:
            dialog = SettingsDialog(self)
            dialog.exec()

        elif selected == combined_action:
            self.storage_mode = "combined"
            self.settings.setValue(
                "storage_mode",
                self.storage_mode
            )
            self.rebuild_storage_rows({})
            self.refresh()

        elif selected == all_action:
            self.storage_mode = "all"
            self.settings.setValue(
                "storage_mode",
                self.storage_mode
            )
            self.rebuild_storage_rows({})
            self.refresh()

        elif selected == lock_action:
            self.locked = not self.locked
            self.settings.setValue(
                "locked",
                self.locked
            )

        elif selected == exit_action:
            QApplication.quit()

    def mousePressEvent(self, event):
        if (
            not self.locked and
            event.button() ==
            Qt.MouseButton.LeftButton
        ):
            self._drag_position = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

            event.accept()

    def mouseMoveEvent(self, event):
        if (
            not self.locked and
            self._drag_position is not None and
            event.buttons() &
            Qt.MouseButton.LeftButton
        ):
            self.move(
                event.globalPosition().toPoint()
                - self._drag_position
            )

            event.accept()

    def mouseReleaseEvent(self, event):
        if self._drag_position is not None:
            self.settings.setValue(
                "position",
                self.pos()
            )

        self._drag_position = None
        event.accept()

    def closeEvent(self, event):
        self.settings.setValue(
            "position",
            self.pos()
        )

        self.settings.setValue(
            "locked",
            self.locked
        )

        super().closeEvent(event)


app = QApplication(sys.argv)
app.setApplicationName("System Status")

window = SystemStatusWindow()
window.show()

sys.exit(app.exec())









