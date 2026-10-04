import sys
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

        footer_font = QFont("Segoe UI", 10)
        footer_font.setBold(True)

        self.system_label.setFont(footer_font)
        self.network_label.setFont(footer_font)

        self.system_label.setStyleSheet(
            "color: white; background: transparent;"
        )

        self.network_label.setStyleSheet(
            "color: white; background: transparent;"
        )

        saved = self.settings.value("position")

        self.rebuild_storage_rows({})

        if isinstance(saved, QPoint):
            self.move(saved)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(
                screen.right() - self.width() - 20,
                screen.top() + 20
            )

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(500)

        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.pulse_warnings)
        self.pulse_timer.start(550)

        self.refresh()

    def usage_state(self, value):
        if value >= CRITICAL_USAGE:
            return "critical"

        if value >= WARNING_USAGE:
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

        footer_y = 66 + max(
            1,
            len(self.storage_rows)
        ) * 22

        self.divider.setGeometry(
            0,
            footer_y + 1,
            510,
            1
        )

        self.system_label.setGeometry(
            0,
            footer_y + 6,
            165,
            22
        )

        self.network_label.setGeometry(
            170,
            footer_y + 6,
            330,
            22
        )

        self.setFixedSize(
            510,
            footer_y + 32
        )

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

        for name, data in network.items():
            if not data.get("up"):
                continue

            lower = name.lower()

            if (
                "tailscale" in lower or
                "proton" in lower or
                "vpn" in lower or
                "wireguard" in lower
            ):
                tunnel_connected = True

            if not data.get("virtual", False):
                if (
                    "ethernet" in lower or
                    "wi-fi" in lower or
                    "wifi" in lower
                ):
                    physical_connected = True

        if not physical_connected:
            state = "OFFLINE"
            color = CRITICAL
        elif tunnel_connected:
            state = "SECURE"
            color = SECURE
        else:
            state = "CONNECTED"
            color = WHITE

        self.network_label.setText(state)
        self.network_label.setStyleSheet(
            f"color: {color}; background: transparent;"
        )

    def refresh(self):
        live = collect_live()

        self.update_row(
            self.rows["cpu"],
            live["cpu"]["usage_percent"]
        )

        self.update_row(
            self.rows["ram"],
            live["memory"]["usage_percent"]
        )

        # Windows GPU utilization provider comes next.
        self.update_row(
            self.rows["gpu"],
            0.0
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

        if selected == combined_action:
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
