import subprocess


CREATE_NO_WINDOW = 0x08000000


def collect_gpu_usage():
    command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        (
            r"(Get-Counter "
            r"'\GPU Engine(*)\Utilization Percentage' "
            r"-ErrorAction SilentlyContinue).CounterSamples | "
            r"Where-Object { "
            r"$_.InstanceName -match 'engtype_(3d|high priority 3d)' "
            r"} | "
            r"ForEach-Object { $_.CookedValue }"
        ),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=3,
            creationflags=CREATE_NO_WINDOW,
        )

        values = []

        for line in result.stdout.splitlines():
            line = line.strip()

            if not line:
                continue

            try:
                values.append(float(line))
            except ValueError:
                pass

        if not values:
            return 0.0

        return round(
            min(max(values), 100.0),
            1
        )

    except (
        subprocess.SubprocessError,
        OSError,
        ValueError,
    ):
        return None
