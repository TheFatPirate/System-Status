from pathlib import Path
import json
import os
import subprocess
import time


SECTOR_SIZE = 512


def read_diskstats():
    result = {}

    try:
        lines = Path("/proc/diskstats").read_text().splitlines()
    except OSError:
        return result

    for line in lines:
        fields = line.split()

        if len(fields) < 14:
            continue

        name = fields[2]

        block_path = Path("/sys/class/block") / name

        if not block_path.exists():
            continue

        # A sysfs "partition" file means this is sda1, nvme0n1p1,
        # etc. System Status publishes physical-drive I/O separately from
        # filesystem/mount usage.
        if (block_path / "partition").exists():
            continue

        # Ignore virtual devices here. zram, loop, dm-* and similar
        # devices can receive dedicated providers later if useful.
        try:
            device_path = block_path.resolve()
        except OSError:
            continue

        if "/virtual/" in str(device_path):
            continue

        try:
            reads_completed = int(fields[3])
            sectors_read = int(fields[5])
            writes_completed = int(fields[7])
            sectors_written = int(fields[9])
        except ValueError:
            continue

        result[name] = {
            "reads": reads_completed,
            "read_bytes": sectors_read * SECTOR_SIZE,
            "writes": writes_completed,
            "write_bytes": sectors_written * SECTOR_SIZE,
        }

    return result


def collect_filesystems(registry):
    try:
        mounts = Path("/proc/self/mounts").read_text().splitlines()
    except OSError:
        return

    seen = set()

    for line in mounts:
        fields = line.split()

        if len(fields) < 3:
            continue

        device, mountpoint, fstype = fields[:3]

        if not device.startswith("/dev/"):
            continue

        if mountpoint in seen:
            continue

        seen.add(mountpoint)

        try:
            stats = os.statvfs(mountpoint)
        except OSError:
            continue

        total = stats.f_blocks * stats.f_frsize
        available = stats.f_bavail * stats.f_frsize
        used = total - (stats.f_bfree * stats.f_frsize)

        if total <= 0:
            continue

        usage = round((used / total) * 100, 1)

        if mountpoint == "/":
            prefix = "storage.root"
            name = "Root Filesystem"
        else:
            safe = (
                mountpoint.strip("/")
                .replace("/", ".")
                .replace(" ", "_")
            )

            if not safe:
                safe = "root"

            prefix = f"storage.mount.{safe}"
            name = mountpoint

        registry.add(
            f"{prefix}.usage",
            usage,
            name=f"{name} Usage",
            category="storage",
            unit="%",
            minimum=0,
            maximum=100,
            warning=80,
            critical=90,
            source="statvfs",
        )

        registry.add(
            f"{prefix}.used",
            used,
            name=f"{name} Used",
            category="storage",
            unit="B",
            source="statvfs",
        )

        registry.add(
            f"{prefix}.total",
            total,
            name=f"{name} Total",
            category="storage",
            unit="B",
            source="statvfs",
        )

        registry.add(
            f"{prefix}.available",
            available,
            name=f"{name} Available",
            category="storage",
            unit="B",
            source="statvfs",
        )

        registry.add(
            f"{prefix}.filesystem",
            fstype,
            name=f"{name} Filesystem",
            category="storage",
            source="/proc/self/mounts",
        )


def collect_rates(registry):
    first = read_diskstats()
    started = time.monotonic()

    time.sleep(0.20)

    second = read_diskstats()
    elapsed = time.monotonic() - started

    if elapsed <= 0:
        return

    for disk, current in second.items():
        previous = first.get(disk)

        if previous is None:
            continue

        read_rate = max(
            0,
            round(
                (
                    current["read_bytes"]
                    - previous["read_bytes"]
                ) / elapsed
            ),
        )

        write_rate = max(
            0,
            round(
                (
                    current["write_bytes"]
                    - previous["write_bytes"]
                ) / elapsed
            ),
        )

        read_iops = max(
            0,
            round(
                (
                    current["reads"]
                    - previous["reads"]
                ) / elapsed,
                1,
            ),
        )

        write_iops = max(
            0,
            round(
                (
                    current["writes"]
                    - previous["writes"]
                ) / elapsed,
                1,
            ),
        )

        prefix = f"storage.{disk}"

        registry.add(
            f"{prefix}.read.rate",
            read_rate,
            name=f"{disk} Read Rate",
            category="storage",
            unit="B/s",
            source="/proc/diskstats",
        )

        registry.add(
            f"{prefix}.write.rate",
            write_rate,
            name=f"{disk} Write Rate",
            category="storage",
            unit="B/s",
            source="/proc/diskstats",
        )

        registry.add(
            f"{prefix}.read.iops",
            read_iops,
            name=f"{disk} Read IOPS",
            category="storage",
            unit="IOPS",
            source="/proc/diskstats",
        )

        registry.add(
            f"{prefix}.write.iops",
            write_iops,
            name=f"{disk} Write IOPS",
            category="storage",
            unit="IOPS",
            source="/proc/diskstats",
        )


def smart_json(device):
    try:
        result = subprocess.run(
            [
                "smartctl",
                "-a",
                "-j",
                f"/dev/{device}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if not result.stdout.strip():
            return None

        return json.loads(result.stdout)

    except (
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ):
        return None


def collect_smart(registry):
    for disk in sorted(read_diskstats()):
        data = smart_json(disk)

        if not data:
            continue

        prefix = f"storage.{disk}"

        model = data.get("model_name")

        if model:
            registry.add(
                f"{prefix}.model",
                model,
                name=f"{disk} Model",
                category="storage",
                source="smartctl",
            )

        health = (
            data.get("smart_status", {})
            .get("passed")
        )

        if health is not None:
            registry.add(
                f"{prefix}.health",
                "PASSED" if health else "FAILED",
                name=f"{disk} SMART Health",
                category="storage",
                source="smartctl",
            )

        temperature = (
            data.get("temperature", {})
            .get("current")
        )

        if temperature is not None:
            registry.add(
                f"{prefix}.temperature",
                temperature,
                name=f"{disk} Temperature",
                category="storage",
                unit="°C",
                warning=60,
                critical=70,
                source="smartctl",
            )

        power_cycles = (
            data.get("power_cycle_count")
        )

        if power_cycles is not None:
            registry.add(
                f"{prefix}.power_cycles",
                power_cycles,
                name=f"{disk} Power Cycles",
                category="storage",
                source="smartctl",
            )

        power_hours = (
            data.get("power_on_time", {})
            .get("hours")
        )

        if power_hours is not None:
            registry.add(
                f"{prefix}.power_on_hours",
                power_hours,
                name=f"{disk} Power-On Hours",
                category="storage",
                unit="h",
                source="smartctl",
            )


def collect(registry):
    collect_filesystems(registry)
    collect_rates(registry)
    collect_smart(registry)
