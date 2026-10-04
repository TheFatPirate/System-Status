import sys
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from hardware import collect_hardware
from live import collect_live


class Metric(QFrame):
    def __init__(self, title):
        super().__init__()

        self.setObjectName("metric")

        layout = QVBoxLayout(self)

        self.title = QLabel(title)
        self.title.setObjectName("metricTitle")

        self.value = QLabel("--")
        self.value.setObjectName("metricValue")

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.bar)

    def update_value(self, value, suffix="%"):
        value = float(value)
        self.value.setText(f"{value:.1f}{suffix}")
        self.bar.setValue(round(value))


class SystemStatusWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.hardware = collect_hardware()

        self.setWindowTitle("System Status")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.resize(520, 500)

        self._drag_position = None

        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("SYSTEM STATUS")
        title.setObjectName("title")
        layout.addWidget(title)

        cpu_name = self.hardware["cpu"][0]["name"]
        gpu_name = self.hardware["gpu"][0]["name"]

        self.cpu_name = QLabel(cpu_name)
        self.cpu_name.setObjectName("hardware")

        self.gpu_name = QLabel(gpu_name)
        self.gpu_name.setObjectName("hardware")

        layout.addWidget(self.cpu_name)
        layout.addWidget(self.gpu_name)

        metrics = QHBoxLayout()

        self.cpu = Metric("CPU")
        self.memory = Metric("MEMORY")

        metrics.addWidget(self.cpu)
        metrics.addWidget(self.memory)

        layout.addLayout(metrics)

        self.storage = QLabel()
        self.storage.setObjectName("details")
        layout.addWidget(self.storage)

        self.network = QLabel()
        self.network.setObjectName("details")
        layout.addWidget(self.network)

        layout.addStretch()

        self.footer = QLabel("System Status 1.0.0 • Windows")
        self.footer.setObjectName("footer")
        layout.addWidget(self.footer)

        self.setStyleSheet("""
            QWidget {
                background: #101417;
                color: #e8f7f7;
                font-family: "Segoe UI";
            }

            QLabel#title {
                font-size: 26px;
                font-weight: 700;
                color: #28d7d7;
            }

            QLabel#hardware {
                font-size: 14px;
                color: #aebfc3;
            }

            QFrame#metric {
                background: #171e22;
                border: 1px solid #26363c;
                border-radius: 8px;
            }

            QLabel#metricTitle {
                color: #7e979e;
                font-size: 12px;
                font-weight: 600;
            }

            QLabel#metricValue {
                color: #28d7d7;
                font-size: 30px;
                font-weight: 700;
            }

            QProgressBar {
                background: #263238;
                border: none;
                border-radius: 4px;
            }

            QProgressBar::chunk {
                background: #28d7d7;
                border-radius: 4px;
            }

            QLabel#details {
                background: #171e22;
                border: 1px solid #26363c;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
            }

            QLabel#footer {
                color: #61757b;
                font-size: 11px;
            }
        """)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)

        self.refresh()

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        exit_action = menu.addAction("Exit System Status")
        selected = menu.exec(event.globalPos())

        if selected == exit_action:
            QApplication.quit()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if (
            self._drag_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            self.move(
                event.globalPosition().toPoint()
                - self._drag_position
            )
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_position = None
        event.accept()
    def refresh(self):
        live = collect_live()

        self.cpu.update_value(live["cpu"]["usage_percent"])
        self.memory.update_value(live["memory"]["usage_percent"])

        storage_lines = ["STORAGE"]

        for drive in live["storage"].values():
            total = drive["total_bytes"] / (1024 ** 3)
            free = drive["free_bytes"] / (1024 ** 3)

            storage_lines.append(
                f'{drive["device"]}  '
                f'{drive["usage_percent"]:.1f}% used  •  '
                f'{free:.0f} GB free / {total:.0f} GB'
            )

        self.storage.setText("\n".join(storage_lines))

        network_lines = ["NETWORK"]

        for name, data in live["network"].items():
            if not data["up"]:
                continue

            if data["virtual"]:
                network_lines.append(f"{name}  •  ACTIVE")
            else:
                network_lines.append(
                    f'{name}  •  CONNECTED  •  {data["speed_mbps"]} Mbps'
                )

        self.network.setText("\n".join(network_lines))


app = QApplication(sys.argv)
app.setApplicationName("System Status")

window = SystemStatusWindow()
window.show()

sys.exit(app.exec())





