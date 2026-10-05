#!/usr/bin/env python3

import copy
import json
from pathlib import Path

import config


CATEGORY_ORDER = {
    "system": 10,
    "cpu": 20,
    "memory": 30,
    "gpu": 40,
    "storage": 50,
    "network": 60,
    "display": 70,
    "gaming": 80,
    "power": 90,
    "sensor": 100,
    "peripheral": 110,
}


def load_snapshot(path):
    path = Path(path)

    try:
        data = json.loads(
            path.read_text()
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
    ):
        return {
            "schema": 1,
            "timestamp": None,
            "sensors": {},
        }

    if not isinstance(data, dict):
        return {
            "schema": 1,
            "timestamp": None,
            "sensors": {},
        }

    sensors = data.get(
        "sensors",
        {},
    )

    if not isinstance(sensors, dict):
        sensors = {}

    return {
        "schema": data.get(
            "schema",
            1,
        ),
        "timestamp": data.get(
            "timestamp"
        ),
        "sensors": sensors,
    }


def merge_snapshots(*snapshots):
    sensors = {}

    timestamps = []

    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue

        timestamp = snapshot.get(
            "timestamp"
        )

        if isinstance(
            timestamp,
            (int, float),
        ):
            timestamps.append(timestamp)

        source_sensors = snapshot.get(
            "sensors",
            {},
        )

        if not isinstance(
            source_sensors,
            dict,
        ):
            continue

        for sensor_id, sensor in (
            source_sensors.items()
        ):
            if not isinstance(
                sensor,
                dict,
            ):
                continue

            sensors[sensor_id] = (
                copy.deepcopy(sensor)
            )

    return {
        "schema": 1,
        "timestamp": (
            max(timestamps)
            if timestamps
            else None
        ),
        "sensors": sensors,
    }


def category_rank(category):
    return CATEGORY_ORDER.get(
        category,
        1000,
    )


def sensor_sort_key(sensor):
    display = sensor.get(
        "display",
        {},
    )

    order = display.get(
        "order"
    )

    if order is None:
        order = 100000

    return (
        category_rank(
            sensor.get(
                "category",
                "",
            )
        ),
        order,
        sensor.get(
            "display_name",
            sensor.get(
                "name",
                "",
            ),
        ).lower(),
        sensor.get(
            "id",
            "",
        ),
    )


def build_sensor_list(
    merged_snapshot,
    user_config,
    *,
    include_disabled=False,
):
    result = []

    sensors = merged_snapshot.get(
        "sensors",
        {},
    )

    show_unavailable = (
        user_config
        .get("general", {})
        .get(
            "show_unavailable",
            False,
        )
    )

    for sensor_id, sensor in (
        sensors.items()
    ):
        if not isinstance(
            sensor,
            dict,
        ):
            continue

        effective = (
            config.effective_sensor(
                sensor,
                user_config,
            )
        )

        display = effective.get(
            "display",
            {},
        )

        enabled = bool(
            display.get(
                "enabled",
                False,
            )
        )

        available = bool(
            effective.get(
                "available",
                True,
            )
        )

        if (
            not include_disabled
            and not enabled
        ):
            continue

        if (
            not available
            and not show_unavailable
        ):
            continue

        result.append(effective)

    result.sort(
        key=sensor_sort_key
    )

    return result


def build_categories(sensors):
    categories = {}

    for sensor in sensors:
        category = sensor.get(
            "category",
            "other",
        )

        categories.setdefault(
            category,
            [],
        ).append(sensor)

    ordered = []

    for category in sorted(
        categories,
        key=lambda name: (
            category_rank(name),
            name,
        ),
    ):
        ordered.append(
            {
                "id": category,
                "sensors": categories[
                    category
                ],
            }
        )

    return ordered


def build_model(
    system_snapshot,
    session_snapshot,
    user_config,
):
    merged = merge_snapshots(
        system_snapshot,
        session_snapshot,
    )

    visible = build_sensor_list(
        merged,
        user_config,
        include_disabled=False,
    )

    all_sensors = build_sensor_list(
        merged,
        user_config,
        include_disabled=True,
    )

    return {
        "schema": 1,
        "timestamp": merged.get(
            "timestamp"
        ),
        "general": copy.deepcopy(
            user_config.get(
                "general",
                {},
            )
        ),
        "appearance": copy.deepcopy(
            user_config.get(
                "appearance",
                {},
            )
        ),
        "visible_sensors": visible,
        "categories": build_categories(
            visible
        ),
        "all_sensors": all_sensors,
    }
