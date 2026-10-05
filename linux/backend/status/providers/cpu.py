from pathlib import Path
import time


def read_number(path, divisor=1):
    try:
        return float(Path(path).read_text().strip()) / divisor
    except (OSError, ValueError):
        return None


def read_cpu_times():
    result = {}

    try:
        lines = Path("/proc/stat").read_text().splitlines()
    except OSError:
        return result

    for line in lines:
        fields = line.split()

        if not fields:
            continue

        name = fields[0]

        if name != "cpu" and not (
            name.startswith("cpu") and name[3:].isdigit()
        ):
            continue

        try:
            values = [int(value) for value in fields[1:]]
        except ValueError:
            continue

        if len(values) < 4:
            continue

        idle = values[3]

        if len(values) > 4:
            idle += values[4]

        total = sum(values)

        result[name] = (total, idle)

    return result


def calculate_usage(first, second):
    result = {}

    for name, (total2, idle2) in second.items():
        if name not in first:
            continue

        total1, idle1 = first[name]

        total_delta = total2 - total1
        idle_delta = idle2 - idle1

        if total_delta <= 0:
            continue

        usage = (
            (total_delta - idle_delta)
            / total_delta
            * 100
        )

        result[name] = round(
            max(0, min(100, usage)),
            1
        )

    return result


def collect_usage(registry):
    first = read_cpu_times()

    if not first:
        return

    time.sleep(0.20)

    second = read_cpu_times()

    for cpu, usage in calculate_usage(first, second).items():
        if cpu == "cpu":
            sensor_id = "cpu.total.usage"
            name = "CPU Usage"
        else:
            number = int(cpu[3:])
            sensor_id = f"cpu.core.{number}.usage"
            name = f"CPU Core {number} Usage"

        registry.add(
            sensor_id,
            usage,
            name=name,
            category="cpu",
            unit="%",
            minimum=0,
            maximum=100,
            warning=75,
            critical=90,
            source="/proc/stat",
        )


def collect_frequency(registry):
    cpu_root = Path("/sys/devices/system/cpu")

    for cpu in sorted(cpu_root.glob("cpu[0-9]*")):
        try:
            number = int(cpu.name[3:])
        except ValueError:
            continue

        freq = read_number(
            cpu / "cpufreq/scaling_cur_freq",
            1000
        )

        if freq is None:
            freq = read_number(
                cpu / "cpufreq/cpuinfo_cur_freq",
                1000
            )

        if freq is not None:
            registry.add(
                f"cpu.core.{number}.frequency",
                round(freq),
                name=f"CPU Core {number} Frequency",
                category="cpu",
                unit="MHz",
                source="sysfs",
            )


def safe_sensor_name(value):
    result = []

    for char in value.lower():
        if char.isalnum():
            result.append(char)
        elif result and result[-1] != "_":
            result.append("_")

    return "".join(result).strip("_") or "unknown"


def read_hwmon_temperature(temp_file):
    try:
        value = float(
            temp_file.read_text().strip()
        ) / 1000
    except (OSError, ValueError):
        return None

    # Reject obviously invalid hwmon values.
    if value < -50 or value > 150:
        return None

    return round(value, 1)


def collect_coretemp(registry, hwmon):
    for temp_file in sorted(
        hwmon.glob("temp*_input")
    ):
        prefix = (
            temp_file.name
            .removesuffix("_input")
        )

        label_file = (
            hwmon
            / f"{prefix}_label"
        )

        try:
            label = (
                label_file
                .read_text()
                .strip()
            )
        except OSError:
            continue

        temp = read_hwmon_temperature(
            temp_file
        )

        if temp is None:
            continue

        if label.startswith(
            "Package id "
        ):
            package = (
                label.split()[-1]
            )

            sensor_id = (
                f"cpu.package."
                f"{package}.temperature"
            )

            name = (
                f"CPU Package "
                f"{package} Temperature"
            )

        elif label.startswith(
            "Core "
        ):
            core = label.split()[-1]

            sensor_id = (
                f"cpu.core."
                f"{core}.temperature"
            )

            name = (
                f"CPU Core "
                f"{core} Temperature"
            )

        else:
            sensor_id = (
                "cpu.sensor."
                + safe_sensor_name(label)
                + ".temperature"
            )

            name = (
                f"CPU {label} Temperature"
            )

        registry.add(
            sensor_id,
            temp,
            name=name,
            category="cpu",
            unit="°C",
            warning=80,
            critical=95,
            source="hwmon",
        )


def collect_k10temp(
    registry,
    hwmon,
    package,
):
    temperatures = []

    for temp_file in sorted(
        hwmon.glob("temp*_input")
    ):
        prefix = (
            temp_file.name
            .removesuffix("_input")
        )

        label_file = (
            hwmon
            / f"{prefix}_label"
        )

        try:
            label = (
                label_file
                .read_text()
                .strip()
            )
        except OSError:
            label = prefix

        temp = read_hwmon_temperature(
            temp_file
        )

        if temp is None:
            continue

        temperatures.append(
            (
                label,
                temp,
            )
        )

        registry.add(
            (
                f"cpu.package.{package}"
                f".sensor."
                f"{safe_sensor_name(label)}"
                ".temperature"
            ),
            temp,
            name=(
                f"CPU Package {package} "
                f"{label} Temperature"
            ),
            category="cpu",
            unit="°C",
            warning=80,
            critical=95,
            source="hwmon",
        )

    if not temperatures:
        return

    # AMD commonly exposes Tdie and/or Tctl.
    # Prefer Tdie as the representative package
    # temperature, then Tctl, then any available
    # thermal reading.

    preferred = None

    for wanted in (
        "tdie",
        "tctl",
    ):
        for label, temp in temperatures:
            if label.lower() == wanted:
                preferred = temp
                break

        if preferred is not None:
            break

    if preferred is None:
        preferred = temperatures[0][1]

    registry.add(
        f"cpu.package.{package}.temperature",
        preferred,
        name=(
            f"CPU Package {package} Temperature"
        ),
        category="cpu",
        unit="°C",
        warning=80,
        critical=95,
        source="hwmon",
    )


def collect_temperature(registry):
    amd_package = 0

    for hwmon in sorted(
        Path("/sys/class/hwmon")
        .glob("hwmon*")
    ):
        try:
            driver = (
                (hwmon / "name")
                .read_text()
                .strip()
            )
        except OSError:
            continue

        if driver == "coretemp":
            collect_coretemp(
                registry,
                hwmon,
            )

        elif driver == "k10temp":
            collect_k10temp(
                registry,
                hwmon,
                amd_package,
            )

            amd_package += 1


def collect(registry):
    collect_usage(registry)
    collect_frequency(registry)
    collect_temperature(registry)
