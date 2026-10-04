import json
import platform
import psutil


def collect():
    memory = psutil.virtual_memory()
    root = psutil.disk_usage("C:\\")

    return {
        "schema": 1,
        "platform": "windows",
        "sensors": {
            "system.os": {
                "value": platform.system()
            },
            "system.release": {
                "value": platform.release()
            },
            "system.version": {
                "value": platform.version()
            },
            "cpu.total.usage": {
                "value": psutil.cpu_percent(interval=1.0),
                "unit": "%"
            },
            "cpu.logical.count": {
                "value": psutil.cpu_count(logical=True)
            },
            "memory.ram.usage": {
                "value": memory.percent,
                "unit": "%"
            },
            "memory.ram.total": {
                "value": memory.total,
                "unit": "B"
            },
            "storage.c.usage": {
                "value": root.percent,
                "unit": "%"
            },
            "storage.c.total": {
                "value": root.total,
                "unit": "B"
            }
        }
    }


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2))
