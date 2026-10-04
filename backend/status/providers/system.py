from pathlib import Path
import os
import platform


def collect(registry):
    version = "unknown"

    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("VERSION_ID="):
                version = line.split("=", 1)[1].strip().strip('"')
                break
    except OSError:
        pass

    registry.add(
        "system.version",
        version,
        name="System Version",
        category="system",
        source="/etc/os-release",
    )

    registry.add(
        "system.kernel",
        platform.release(),
        name="Kernel",
        category="system",
        source="uname",
    )

    try:
        uptime = float(
            Path("/proc/uptime").read_text().split()[0]
        )
        registry.add(
            "system.uptime",
            int(uptime),
            name="Uptime",
            category="system",
            unit="s",
            source="/proc/uptime",
        )
    except (OSError, ValueError, IndexError):
        pass

    try:
        load1, load5, load15 = os.getloadavg()

        for sensor_id, name, value in (
            ("system.load.1", "1 Minute Load", load1),
            ("system.load.5", "5 Minute Load", load5),
            ("system.load.15", "15 Minute Load", load15),
        ):
            registry.add(
                sensor_id,
                round(value, 2),
                name=name,
                category="system",
                source="/proc/loadavg",
            )
    except OSError:
        pass
