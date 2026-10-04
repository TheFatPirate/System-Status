from pathlib import Path
import subprocess
import time


NET_ROOT = Path("/sys/class/net")


def read_int(path):
    try:
        return int(Path(path).read_text().strip())
    except (OSError, ValueError):
        return None


def read_counters():
    counters = {}

    for interface in NET_ROOT.iterdir():
        name = interface.name

        if name == "lo":
            continue

        rx = read_int(
            interface / "statistics/rx_bytes"
        )
        tx = read_int(
            interface / "statistics/tx_bytes"
        )

        if rx is not None and tx is not None:
            counters[name] = (rx, tx)

    return counters


def collect(registry):
    first = read_counters()
    started = time.monotonic()

    time.sleep(0.20)

    second = read_counters()
    elapsed = time.monotonic() - started

    if elapsed <= 0:
        elapsed = 0.20

    for interface, (rx2, tx2) in second.items():
        if interface not in first:
            continue

        rx1, tx1 = first[interface]

        rx_rate = max(
            0,
            round((rx2 - rx1) / elapsed)
        )
        tx_rate = max(
            0,
            round((tx2 - tx1) / elapsed)
        )

        prefix = f"network.{interface}"

        registry.add(
            f"{prefix}.rx.rate",
            rx_rate,
            name=f"{interface} Download",
            category="network",
            unit="B/s",
            source="sysfs",
        )

        registry.add(
            f"{prefix}.tx.rate",
            tx_rate,
            name=f"{interface} Upload",
            category="network",
            unit="B/s",
            source="sysfs",
        )

        speed = read_int(
            NET_ROOT / interface / "speed"
        )

        if speed is not None and speed >= 0:
            registry.add(
                f"{prefix}.link.speed",
                speed,
                name=f"{interface} Link Speed",
                category="network",
                unit="Mb/s",
                source="sysfs",
            )

    vpn_secure = False

    try:
        output = subprocess.run(
            [
                "nmcli",
                "-t",
                "-f",
                "DEVICE,TYPE,STATE",
                "device",
                "status",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        ).stdout

        vpn_secure = (
            "proton0:wireguard:connected"
            in output
        )
    except (OSError, subprocess.SubprocessError):
        pass

    registry.add(
        "network.security",
        "SECURE" if vpn_secure else "OFFLINE",
        name="Network Security",
        category="network",
        source="NetworkManager",
    )

    registry.add(
        "network.vpn.active",
        vpn_secure,
        name="VPN Active",
        category="network",
        source="NetworkManager",
    )
