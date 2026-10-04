#!/usr/bin/env python3

import json
import time


class SensorRegistry:
    def __init__(self):
        self.sensors = {}

    def add(
        self,
        sensor_id,
        value,
        *,
        name,
        category,
        unit="",
        available=True,
        source="",
        minimum=None,
        maximum=None,
        warning=None,
        critical=None,
    ):
        self.sensors[sensor_id] = {
            "id": sensor_id,
            "name": name,
            "category": category,
            "value": value,
            "unit": unit,
            "available": available,
            "source": source,
            "minimum": minimum,
            "maximum": maximum,
            "warning": warning,
            "critical": critical,
        }

    def snapshot(self):
        return {
            "schema": 1,
            "timestamp": time.time(),
            "sensors": self.sensors,
        }

    def json(self):
        return json.dumps(
            self.snapshot(),
            indent=2,
            sort_keys=True
        )
