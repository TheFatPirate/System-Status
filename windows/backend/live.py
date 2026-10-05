import psutil


def collect_live():
    memory = psutil.virtual_memory()

    result = {
        "cpu": {
            "usage_percent": psutil.cpu_percent(interval=0.5),
            "logical_processors": psutil.cpu_count(logical=True)
        },
        "memory": {
            "usage_percent": memory.percent,
            "total_bytes": memory.total,
            "available_bytes": memory.available,
            "used_bytes": memory.used
        },
        "storage": {},
        "network": {}
    }

    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue

        key = part.device.rstrip("\\").replace(":", "").lower()

        result["storage"][key] = {
            "device": part.device,
            "filesystem": part.fstype,
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "usage_percent": usage.percent
        }

    stats = psutil.net_if_stats()
    counters = psutil.net_io_counters(pernic=True)

    for name in psutil.net_if_addrs():
        stat = stats.get(name)
        io = counters.get(name)

        if not stat:
            continue

        lower = name.lower()

        virtual = (
            "tailscale" in lower
            or "loopback" in lower
            or "local area connection*" in lower
        )

        result["network"][name] = {
            "up": stat.isup,
            "virtual": virtual,
            "speed_mbps": stat.speed if not virtual else None,
            "bytes_sent": io.bytes_sent if io else 0,
            "bytes_received": io.bytes_recv if io else 0
        }

    return result
