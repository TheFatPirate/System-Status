#!/usr/bin/env python3

import copy
import json
import os
from pathlib import Path


CONFIG_SCHEMA = 1

DEFAULT_CONFIG = {
    "schema": CONFIG_SCHEMA,

    "general": {
        "refresh_ms": 500,
        "show_unavailable": False,
        "show_category_headers": True,
    },

    "appearance": {
        "compact": False,
        "show_units": True,
        "show_icons": True,
    },

    # Per-sensor overrides only.
    #
    # Sensors not present here use registry/default behavior.
    #
    # Example:
    #
    # "cpu.total.usage": {
    #     "enabled": True,
    #     "order": 10,
    #     "name": "CPU",
    #     "format": "value",
    #     "unit": "%",
    #     "warning": 80,
    #     "critical": 95,
    # }
    "sensors": {},
}


SENSOR_DEFAULTS = {
    "enabled": False,
    "order": None,
    "name": None,
    "format": "value",
    "unit": None,
    "warning": None,
    "critical": None,
    "device": None,
}


VALID_FORMATS = {
    "value",
    "raw",
    "percent",
    "value_percent",
}


def config_directory():
    base = os.environ.get("XDG_CONFIG_HOME")

    if base:
        return Path(base) / "system-status"

    return Path.home() / ".config" / "system-status"


def config_file():
    return config_directory() / "status.json"


def deep_merge(base, override):
    result = copy.deepcopy(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(
                result[key],
                value,
            )
        else:
            result[key] = copy.deepcopy(value)

    return result


def normalize_sensor_config(value):
    if not isinstance(value, dict):
        value = {}

    result = copy.deepcopy(SENSOR_DEFAULTS)

    for key in SENSOR_DEFAULTS:
        if key in value:
            result[key] = value[key]

    result["enabled"] = bool(
        result["enabled"]
    )

    if result["order"] is not None:
        try:
            result["order"] = int(
                result["order"]
            )
        except (TypeError, ValueError):
            result["order"] = None

    if result["format"] not in VALID_FORMATS:
        result["format"] = "value"

    for key in (
        "warning",
        "critical",
    ):
        value = result[key]

        if value is not None:
            try:
                result[key] = float(value)
            except (TypeError, ValueError):
                result[key] = None

    for key in (
        "name",
        "unit",
        "device",
    ):
        value = result[key]

        if value is not None:
            result[key] = str(value)

    return result


def normalize_config(value):
    if not isinstance(value, dict):
        value = {}

    result = deep_merge(
        DEFAULT_CONFIG,
        value,
    )

    result["schema"] = CONFIG_SCHEMA

    general = result["general"]

    try:
        refresh_ms = int(
            general.get(
                "refresh_ms",
                500,
            )
        )
    except (TypeError, ValueError):
        refresh_ms = 500

    general["refresh_ms"] = max(
        250,
        min(
            refresh_ms,
            30000,
        ),
    )

    general["show_unavailable"] = bool(
        general.get(
            "show_unavailable",
            False,
        )
    )

    general["show_category_headers"] = bool(
        general.get(
            "show_category_headers",
            True,
        )
    )

    appearance = result["appearance"]

    appearance["compact"] = bool(
        appearance.get(
            "compact",
            False,
        )
    )

    appearance["show_units"] = bool(
        appearance.get(
            "show_units",
            True,
        )
    )

    appearance["show_icons"] = bool(
        appearance.get(
            "show_icons",
            True,
        )
    )

    sensors = result.get(
        "sensors",
        {},
    )

    if not isinstance(sensors, dict):
        sensors = {}

    result["sensors"] = {
        str(sensor_id):
            normalize_sensor_config(
                sensor_config
            )
        for sensor_id, sensor_config
        in sensors.items()
    }

    return result


def load(path=None):
    if path is None:
        path = config_file()

    path = Path(path)

    try:
        raw = json.loads(
            path.read_text()
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
    ):
        raw = {}

    return normalize_config(raw)


def save(config, path=None):
    if path is None:
        path = config_file()

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    normalized = normalize_config(
        config
    )

    temporary = path.with_suffix(
        ".tmp"
    )

    with temporary.open("w") as handle:
        json.dump(
            normalized,
            handle,
            indent=2,
            sort_keys=True,
        )

        handle.write("\n")
        handle.flush()
        os.fsync(
            handle.fileno()
        )

    os.chmod(
        temporary,
        0o600,
    )

    os.replace(
        temporary,
        path,
    )


def sensor_preferences(
    config,
    sensor_id,
):
    sensors = config.get(
        "sensors",
        {},
    )

    return normalize_sensor_config(
        sensors.get(
            sensor_id,
            {},
        )
    )


def effective_sensor(
    sensor,
    config,
):
    result = copy.deepcopy(sensor)

    preferences = sensor_preferences(
        config,
        sensor["id"],
    )

    result["display"] = preferences

    if preferences["name"]:
        result["display_name"] = (
            preferences["name"]
        )
    else:
        result["display_name"] = (
            sensor["name"]
        )

    if preferences["unit"] is not None:
        result["display_unit"] = (
            preferences["unit"]
        )
    else:
        result["display_unit"] = (
            sensor.get(
                "unit",
                "",
            )
        )

    warning = preferences["warning"]

    if warning is None:
        warning = sensor.get(
            "warning"
        )

    critical = preferences["critical"]

    if critical is None:
        critical = sensor.get(
            "critical"
        )

    result["display_warning"] = warning
    result["display_critical"] = critical

    return result
