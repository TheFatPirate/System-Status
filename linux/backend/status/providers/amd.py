from pathlib import Path
import re


def read_int(path):
    try:
        return int(Path(path).read_text().strip())
    except (OSError, ValueError):
        return None


def active_clock(path):
    try:
        text = Path(path).read_text()
    except OSError:
        return None

    for line in text.splitlines():
        if "*" not in line:
            continue

        match = re.search(r"(\d+)\s*Mhz", line, re.I)

        if match:
            return int(match.group(1))

    return None


def collect(registry):
    gpu_index = 0

    for card in sorted(Path("/sys/class/drm").glob("card[0-9]*")):
        device = card / "device"

        if not device.exists():
            continue

        try:
            driver = (device / "driver").resolve().name
        except OSError:
            continue

        if driver != "amdgpu":
            continue

        prefix = f"gpu.{gpu_index}"

        busy = read_int(device / "gpu_busy_percent")

        if busy is not None:
            registry.add(
                f"{prefix}.usage",
                busy,
                name=f"GPU {gpu_index} Usage",
                category="gpu",
                unit="%",
                minimum=0,
                maximum=100,
                warning=90,
                critical=98,
                source="amdgpu",
            )

        for filename, suffix, name in (
            (
                "mem_info_vram_total",
                "vram.total",
                "VRAM Total"
            ),
            (
                "mem_info_vram_used",
                "vram.used",
                "VRAM Used"
            ),
            (
                "mem_info_gtt_total",
                "gtt.total",
                "GTT Total"
            ),
            (
                "mem_info_gtt_used",
                "gtt.used",
                "GTT Used"
            ),
        ):
            value = read_int(device / filename)

            if value is not None:
                registry.add(
                    f"{prefix}.{suffix}",
                    value,
                    name=f"GPU {gpu_index} {name}",
                    category="gpu",
                    unit="B",
                    source="amdgpu",
                )

        core_clock = active_clock(device / "pp_dpm_sclk")
        memory_clock = active_clock(device / "pp_dpm_mclk")

        if core_clock is not None:
            registry.add(
                f"{prefix}.clock.core",
                core_clock,
                name=f"GPU {gpu_index} Core Clock",
                category="gpu",
                unit="MHz",
                source="amdgpu",
            )

        if memory_clock is not None:
            registry.add(
                f"{prefix}.clock.memory",
                memory_clock,
                name=f"GPU {gpu_index} Memory Clock",
                category="gpu",
                unit="MHz",
                source="amdgpu",
            )

        for hwmon in (device / "hwmon").glob("hwmon*"):
            for temp in hwmon.glob("temp*_input"):
                base = temp.name.removesuffix("_input")

                try:
                    value = int(temp.read_text().strip()) / 1000
                    label = (
                        hwmon / f"{base}_label"
                    ).read_text().strip().lower()
                except (OSError, ValueError):
                    continue

                registry.add(
                    f"{prefix}.temperature.{label}",
                    round(value, 1),
                    name=f"GPU {gpu_index} {label.title()} Temperature",
                    category="gpu",
                    unit="°C",
                    warning=80,
                    critical=90,
                    source="amdgpu-hwmon",
                )

            fan = read_int(hwmon / "fan1_input")
            fan_max = read_int(hwmon / "fan1_max")
            pwm = read_int(hwmon / "pwm1")
            pwm_max = read_int(hwmon / "pwm1_max")

            # Some AMD hardware/driver combinations expose tiny
            # non-zero tachometer values while the fan is stopped.
            # Treat those as zero when PWM also reports zero.
            if (
                fan is not None
                and pwm == 0
                and fan < 100
            ):
                fan = 0

            if fan is not None:
                registry.add(
                    f"{prefix}.fan.rpm",
                    fan,
                    name=f"GPU {gpu_index} Fan",
                    category="gpu",
                    unit="RPM",
                    minimum=0,
                    source="amdgpu-hwmon",
                )

            # PWM is the better percentage source when available.
            if (
                pwm is not None
                and pwm_max is not None
                and pwm_max > 0
            ):
                fan_percent = (
                    pwm / pwm_max
                ) * 100

                registry.add(
                    f"{prefix}.fan.percent",
                    round(
                        max(
                            0,
                            min(100, fan_percent),
                        ),
                        1,
                    ),
                    name=f"GPU {gpu_index} Fan Speed",
                    category="gpu",
                    unit="%",
                    minimum=0,
                    maximum=100,
                    source="amdgpu-hwmon",
                )

            elif (
                fan is not None
                and fan_max is not None
                and fan_max > 0
            ):
                registry.add(
                    f"{prefix}.fan.percent",
                    round(
                        max(
                            0,
                            min(
                                100,
                                (fan / fan_max) * 100,
                            ),
                        ),
                        1,
                    ),
                    name=f"GPU {gpu_index} Fan Speed",
                    category="gpu",
                    unit="%",
                    minimum=0,
                    maximum=100,
                    source="amdgpu-hwmon",
                )

            power = read_int(hwmon / "power1_input")

            if power is not None:
                registry.add(
                    f"{prefix}.power",
                    round(power / 1_000_000, 2),
                    name=f"GPU {gpu_index} Power",
                    category="gpu",
                    unit="W",
                    source="amdgpu-hwmon",
                )

            voltage = read_int(hwmon / "in0_input")

            if voltage is not None:
                registry.add(
                    f"{prefix}.voltage",
                    round(voltage / 1000, 3),
                    name=f"GPU {gpu_index} Voltage",
                    category="gpu",
                    unit="V",
                    source="amdgpu-hwmon",
                )

        gpu_index += 1
