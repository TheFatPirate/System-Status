from pathlib import Path


def collect(registry):
    values = {}

    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if ":" not in line:
                continue

            key, rest = line.split(":", 1)
            fields = rest.split()

            if not fields:
                continue

            try:
                values[key] = int(fields[0]) * 1024
            except ValueError:
                continue
    except OSError:
        return

    mappings = (
        ("memory.ram.total", "Total RAM", "MemTotal"),
        ("memory.ram.free", "Free RAM", "MemFree"),
        ("memory.ram.available", "Available RAM", "MemAvailable"),
        ("memory.swap.total", "Total Swap", "SwapTotal"),
        ("memory.swap.free", "Free Swap", "SwapFree"),
    )

    for sensor_id, name, key in mappings:
        if key in values:
            registry.add(
                sensor_id,
                values[key],
                name=name,
                category="memory",
                unit="B",
                source="/proc/meminfo",
            )

    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", 0)

    if total:
        used = total - available

        registry.add(
            "memory.ram.used",
            used,
            name="RAM Used",
            category="memory",
            unit="B",
            source="/proc/meminfo",
        )

        registry.add(
            "memory.ram.usage",
            round((used / total) * 100, 1),
            name="RAM Usage",
            category="memory",
            unit="%",
            minimum=0,
            maximum=100,
            warning=75,
            critical=90,
            source="/proc/meminfo",
        )

    swap_total = values.get("SwapTotal", 0)
    swap_free = values.get("SwapFree", 0)

    if swap_total:
        registry.add(
            "memory.swap.used",
            swap_total - swap_free,
            name="Swap Used",
            category="memory",
            unit="B",
            source="/proc/meminfo",
        )
