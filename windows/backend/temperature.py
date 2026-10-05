import os
import sys
from pathlib import Path

import clr


_computer = None
_sensor_type = None


def _find_lhm():
    candidates = []

    # PyInstaller bundle/runtime location.
    if getattr(sys, "frozen", False):
        bundle_root = Path(
            getattr(sys, "_MEIPASS", Path(sys.executable).parent)
        )

        candidates.extend(
            (
                bundle_root
                / "runtime"
                / "LibreHardwareMonitorLib.dll",

                Path(sys.executable).parent
                / "runtime"
                / "LibreHardwareMonitorLib.dll",
            )
        )

    # Source-tree development location:
    # windows/backend/temperature.py -> windows/runtime/
    candidates.append(
        Path(__file__).resolve().parents[1]
        / "runtime"
        / "LibreHardwareMonitorLib.dll"
    )

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    # Development fallback for machines where LHM was installed
    # separately through WinGet.
    local_appdata = os.environ.get("LOCALAPPDATA")

    if local_appdata:
        base = (
            Path(local_appdata)
            / "Microsoft"
            / "WinGet"
            / "Packages"
        )

        if base.exists():
            matches = list(
                base.glob(
                    "LibreHardwareMonitor.LibreHardwareMonitor_*"
                    "/LibreHardwareMonitorLib.dll"
                )
            )

            if matches:
                return matches[0]

    return None


def _walk(hardware):
    hardware.Update()

    yield hardware

    for sub in hardware.SubHardware:
        yield from _walk(sub)


def _initialize():
    global _computer, _sensor_type

    if _computer is not None:
        return True

    dll = _find_lhm()

    if dll is None:
        return False

    sys.path.insert(0, str(dll.parent))
    clr.AddReference(str(dll))

    from LibreHardwareMonitor.Hardware import (
        Computer,
        SensorType,
    )

    computer = Computer()
    computer.IsCpuEnabled = True
    computer.IsGpuEnabled = True
    computer.IsMotherboardEnabled = True
    computer.IsMemoryEnabled = False
    computer.IsControllerEnabled = False
    computer.IsNetworkEnabled = False
    computer.IsStorageEnabled = False
    computer.Open()

    _computer = computer
    _sensor_type = SensorType

    return True


def collect_temperatures():
    result = {
        "cpu_c": None,
        "gpu_c": None,
        "gpu_hotspot_c": None,
    }

    try:
        if not _initialize():
            return result

        for root in _computer.Hardware:
            for hardware in _walk(root):
                hardware_type = str(
                    hardware.HardwareType
                )

                for sensor in hardware.Sensors:
                    if (
                        sensor.SensorType
                        != _sensor_type.Temperature
                    ):
                        continue

                    if sensor.Value is None:
                        continue

                    value = float(sensor.Value)

                    # Ignore clearly invalid temperature values.
                    if value <= 0:
                        continue

                    name = str(sensor.Name)

                    if (
                        hardware_type == "Cpu"
                        and name == "CPU Package"
                    ):
                        result["cpu_c"] = round(
                            value, 1
                        )

                    elif (
                        hardware_type == "GpuAmd"
                        and name == "GPU Core"
                    ):
                        result["gpu_c"] = round(
                            value, 1
                        )

                    elif (
                        hardware_type == "GpuAmd"
                        and name == "GPU Hot Spot"
                    ):
                        result["gpu_hotspot_c"] = round(
                            value, 1
                        )

        return result

    except Exception:
        return result


def convert_temperature(value_c, unit="C"):
    if value_c is None:
        return None

    if str(unit).upper() == "F":
        return (value_c * 9.0 / 5.0) + 32.0

    return value_c
