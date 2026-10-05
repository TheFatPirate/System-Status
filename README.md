# System Status

**System Status 1.0.0** is a cross-platform desktop system monitor for
**Windows 11** and **Linux / KDE Plasma 6**, maintained by **The Fat Pirate**.

The Windows and Linux implementations share the same project and release, but
each platform has its own native implementation.

---

# Windows

## System Status for Windows 1.0.0

Windows users should download:

    SystemStatus-Windows-Setup-1.0.0.exe

The Windows version is a lightweight desktop widget providing:

- CPU usage and temperature
- RAM usage
- GPU usage and temperature
- GPU hotspot temperature when available
- Individual or combined storage monitoring
- Live network download and upload rates
- ONLINE / SECURE / OFFLINE network status
- Configurable warning and critical thresholds
- Configurable widget layout
- Movable and lockable desktop widget
- Optional desktop shortcut
- Optional automatic startup with Windows

The installer includes the required runtime components. Python and
LibreHardwareMonitor do not need to be installed separately.

Windows source and documentation:

    windows/

See `windows/README.md` for additional Windows information.

---

# Linux

## System Status for Linux 1.0.0

The Linux version is a KDE Plasma 6 desktop widget.

It has been built and validated on:

- Fedora 44 x86_64
- KDE Plasma 6

Linux users should download:

    system-status-widget-1.0.0-1.fc44.x86_64.rpm

Install with:

    sudo dnf install ./system-status-widget-1.0.0-1.fc44.x86_64.rpm

Linux features include:

- CPU usage, frequency, and temperature
- RAM and swap usage
- Storage telemetry
- Display resolution, refresh rate, brightness, HDR, VRR, and scale
- Network receive and transmit activity
- Network link speed
- VPN-aware network security state
- GameMode availability and state
- MangoHud availability and gaming telemetry
- Separate system and graphical-session telemetry services

Linux source:

    linux/

The Linux telemetry services are:

    system-status-v2.service
    system-status-session-v2.service

---

# Repository layout

    System-Status/
    |
    +-- linux/          Linux / KDE Plasma 6 implementation
    |   +-- backend/
    |   +-- contents/
    |   +-- packaging/
    |   `-- metadata.json
    |
    +-- windows/        Windows 11 implementation
    |   +-- backend/
    |   +-- ui/
    |   +-- installer/
    |   +-- runtime/
    |   `-- licenses/
    |
    +-- SystemStatus.spec
    +-- LICENSE
    `-- README.md

# Release

System Status 1.0.0 provides both Windows and Linux builds under the same
release.

Windows:

    SystemStatus-Windows-Setup-1.0.0.exe

Linux:

    system-status-widget-1.0.0-1.fc44.x86_64.rpm

# License

System Status is released under the MIT License.

See `LICENSE` for the full license text.

The Windows distribution includes LibreHardwareMonitor components under their
applicable licenses. Third-party notices are included under `windows/licenses/`
and `windows/THIRD-PARTY-NOTICES.md`.

# Maintainer

**The Fat Pirate**
