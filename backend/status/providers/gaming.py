import csv
import os
import re
import shutil
import subprocess
import time
from pathlib import Path


def command_version(command, args):
    path = shutil.which(command)

    if path is None:
        return None, None

    try:
        result = subprocess.run(
            [path, *args],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )

        text = (
            result.stdout.strip()
            or result.stderr.strip()
        )

        return path, text

    except (OSError, subprocess.SubprocessError):
        return path, None


def collect_capabilities(registry):
    mangohud_path, mangohud_version = command_version(
        "mangohud",
        ["--version"],
    )

    registry.add(
        "gaming.mangohud.available",
        mangohud_path is not None,
        name="MangoHud Available",
        category="gaming",
        source="PATH",
    )

    if mangohud_version:
        registry.add(
            "gaming.mangohud.version",
            mangohud_version,
            name="MangoHud Version",
            category="gaming",
            source="mangohud",
        )

    gamemode_path, gamemode_version = command_version(
        "gamemoded",
        ["--version"],
    )

    registry.add(
        "gaming.gamemode.available",
        gamemode_path is not None,
        name="GameMode Available",
        category="gaming",
        source="PATH",
    )

    if gamemode_version:
        normalized = gamemode_version.strip()
        prefix = "gamemode version:"

        if normalized.lower().startswith(prefix):
            normalized = normalized[len(prefix):].strip()

        registry.add(
            "gaming.gamemode.version",
            normalized,
            name="GameMode Version",
            category="gaming",
            source="gamemoded",
        )


def collect_state(registry):
    gamemode_path = shutil.which("gamemoded")
    gamemode_active = False

    if gamemode_path is not None:
        try:
            result = subprocess.run(
                [gamemode_path, "-s"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )

            output = (
                result.stdout
                + result.stderr
            ).lower()

            gamemode_active = (
                "gamemode is active" in output
                and "inactive" not in output
            )

        except (OSError, subprocess.SubprocessError):
            pass

    registry.add(
        "gaming.gamemode.active",
        gamemode_active,
        name="GameMode Active",
        category="gaming",
        source="gamemoded",
    )


def percentile(values, percent):
    if not values:
        return None

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (
        (len(ordered) - 1)
        * (percent / 100.0)
    )

    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower

    return (
        ordered[lower]
        + (
            ordered[upper]
            - ordered[lower]
        )
        * fraction
    )


def default_mangohud_directory():
    return Path(
        f"/tmp/system-status-mangohud-{os.getuid()}"
    )


def latest_raw_log(directory):
    if directory is None:
        return None

    directory = Path(directory)

    if not directory.is_dir():
        return None

    candidates = [
        path
        for path in directory.glob("*.csv")
        if not path.name.endswith("_summary.csv")
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda path: path.stat().st_mtime,
    )


def read_mangohud_samples(path):
    try:
        lines = path.read_text(
            errors="replace"
        ).splitlines()
    except OSError:
        return []

    header_index = None

    for index, line in enumerate(lines):
        if line.startswith("fps,frametime,"):
            header_index = index
            break

    if header_index is None:
        return []

    reader = csv.DictReader(
        lines[header_index:]
    )

    samples = []

    for row in reader:
        try:
            samples.append(
                {
                    "fps": float(row["fps"]),
                    "frametime": float(
                        row["frametime"]
                    ),
                    "elapsed": int(
                        row.get("elapsed", "0")
                    ),
                }
            )
        except (
            TypeError,
            ValueError,
            KeyError,
        ):
            continue

    return samples


def game_name_from_log(path):
    name = path.stem

    match = re.match(
        r"^(.*?)_\d{4}-\d{2}-\d{2}_"
        r"\d{2}-\d{2}-\d{2}$",
        name,
    )

    if match:
        return match.group(1)

    return name


def collect_frame_telemetry(
    registry,
    directory=None,
    max_age=2.0,
):
    if directory is None:
        directory = default_mangohud_directory()

    path = latest_raw_log(directory)

    if path is None:
        return

    if max_age is not None:
        try:
            age = time.time() - path.stat().st_mtime
        except OSError:
            return

        if age > max_age:
            return

    samples = read_mangohud_samples(path)

    if not samples:
        return

    # 250ms samples × 120 = ~30 seconds.
    recent = samples[-120:]

    fps_values = [
        sample["fps"]
        for sample in recent
    ]

    latest = recent[-1]

    average_fps = (
        sum(fps_values)
        / len(fps_values)
    )

    low_1 = percentile(
        fps_values,
        1.0,
    )

    low_01 = percentile(
        fps_values,
        0.1,
    )

    registry.add(
        "gaming.active",
        True,
        name="Game Telemetry Active",
        category="gaming",
        source="MangoHud",
    )

    registry.add(
        "gaming.application",
        game_name_from_log(path),
        name="Game",
        category="gaming",
        source="MangoHud",
    )

    registry.add(
        "gaming.fps",
        round(latest["fps"], 1),
        unit="FPS",
        name="FPS",
        category="gaming",
        source="MangoHud",
        minimum=0,
    )

    registry.add(
        "gaming.frametime",
        round(latest["frametime"], 2),
        unit="ms",
        name="Frame Time",
        category="gaming",
        source="MangoHud",
        minimum=0,
    )

    registry.add(
        "gaming.fps.average",
        round(average_fps, 1),
        unit="FPS",
        name="Average FPS",
        category="gaming",
        source="MangoHud",
        minimum=0,
    )

    registry.add(
        "gaming.fps.1low",
        round(low_1, 1),
        unit="FPS",
        name="1% Low FPS",
        category="gaming",
        source="MangoHud",
        minimum=0,
    )

    registry.add(
        "gaming.fps.01low",
        round(low_01, 1),
        unit="FPS",
        name="0.1% Low FPS",
        category="gaming",
        source="MangoHud",
        minimum=0,
    )


def collect(registry):
    collect_capabilities(registry)
    collect_state(registry)
    collect_frame_telemetry(registry)
