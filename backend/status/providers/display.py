import re
import subprocess
import time


ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

BACKOFF_BASE = 60
BACKOFF_MAX = 300

_failure_count = 0
_next_retry = 0.0


def _mark_failure(now):
    global _failure_count
    global _next_retry

    _failure_count += 1

    delay = min(
        BACKOFF_BASE * (2 ** (_failure_count - 1)),
        BACKOFF_MAX,
    )

    _next_retry = now + delay


def _mark_success():
    global _failure_count
    global _next_retry

    _failure_count = 0
    _next_retry = 0.0


def collect(registry):
    now = time.monotonic()

    if now < _next_retry:
        return

    try:
        result = subprocess.run(
            ["kscreen-doctor", "-o"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        _mark_failure(now)
        return

    if result.returncode != 0:
        _mark_failure(now)
        return

    text = ANSI_RE.sub("", result.stdout)

    if not text.strip():
        _mark_failure(now)
        return

    _mark_success()

    # Split on each Output: block.
    blocks = re.split(r"(?=Output:\s+\d+)", text)

    display_index = 0

    for block in blocks:
        if not block.startswith("Output:"):
            continue

        prefix = f"display.{display_index}"

        first_line = block.splitlines()[0]

        match = re.match(
            r"Output:\s+\d+\s+(\S+)",
            first_line
        )

        connector = match.group(1) if match else f"display{display_index}"

        registry.add(
            f"{prefix}.connector",
            connector,
            name=f"Display {display_index} Connector",
            category="display",
            source="KScreen",
        )

        geometry = re.search(
            r"Geometry:\s+\d+,\d+\s+(\d+)x(\d+)",
            block
        )

        if geometry:
            width = int(geometry.group(1))
            height = int(geometry.group(2))

            registry.add(
                f"{prefix}.resolution.width",
                width,
                name=f"Display {display_index} Width",
                category="display",
                unit="px",
                source="KScreen",
            )

            registry.add(
                f"{prefix}.resolution.height",
                height,
                name=f"Display {display_index} Height",
                category="display",
                unit="px",
                source="KScreen",
            )

            registry.add(
                f"{prefix}.resolution",
                f"{width}x{height}",
                name=f"Display {display_index} Resolution",
                category="display",
                source="KScreen",
            )

        # Active mode is marked with * in KScreen output.
        mode = re.search(
            r"(\d+)x(\d+)@([0-9.]+)\*",
            block
        )

        if mode:
            refresh = float(mode.group(3))

            registry.add(
                f"{prefix}.refresh",
                round(refresh, 2),
                name=f"Display {display_index} Refresh Rate",
                category="display",
                unit="Hz",
                source="KScreen",
            )

        scale = re.search(
            r"Scale:\s+([0-9.]+)",
            block
        )

        if scale:
            registry.add(
                f"{prefix}.scale",
                float(scale.group(1)),
                name=f"Display {display_index} Scale",
                category="display",
                source="KScreen",
            )

        hdr = re.search(
            r"HDR:\s+(.+)",
            block
        )

        if hdr:
            state = hdr.group(1).strip()

            registry.add(
                f"{prefix}.hdr",
                state,
                name=f"Display {display_index} HDR",
                category="display",
                source="KScreen",
            )

        vrr = re.search(
            r"Vrr:\s+(.+)",
            block,
            re.I
        )

        if vrr:
            state = vrr.group(1).strip()

            registry.add(
                f"{prefix}.vrr",
                state,
                name=f"Display {display_index} VRR",
                category="display",
                source="KScreen",
            )

        brightness = re.search(
            r"Brightness control:\s+supported,\s+set to\s+(\d+)%",
            block,
            re.I
        )

        if brightness:
            registry.add(
                f"{prefix}.brightness",
                int(brightness.group(1)),
                name=f"Display {display_index} Brightness",
                category="display",
                unit="%",
                minimum=0,
                maximum=100,
                source="KScreen",
            )

        display_index += 1
