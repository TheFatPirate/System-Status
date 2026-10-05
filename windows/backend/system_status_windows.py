import json
import platform

from hardware import collect_hardware
from live import collect_live


SCHEMA_VERSION = 1
SYSTEM_STATUS_VERSION = "1.0.0"


def collect():
    return {
        "schema": SCHEMA_VERSION,
        "version": SYSTEM_STATUS_VERSION,
        "platform": "windows",
        "system": {
            "os": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine()
        },
        "hardware": collect_hardware(),
        "live": collect_live()
    }


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2))
