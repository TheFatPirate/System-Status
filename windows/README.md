# System Status for Windows

**System Status for Windows 1.0.0** is the Windows desktop implementation of
System Status by **The Fat Pirate**.

It provides a lightweight, always-available desktop view of current system
resource and hardware information.

## Features

- CPU usage
- CPU temperature when supported by the hardware
- RAM usage
- GPU usage
- GPU temperature when supported by the hardware
- Storage utilization
- Individual or combined storage display
- Live network download activity
- Live network upload activity
- Network connection state
- Configurable warning and critical thresholds
- Celsius and Fahrenheit temperature display
- Configurable telemetry visibility
- Movable desktop widget
- Lockable widget position
- Optional startup with Windows

Hardware sensor availability can vary by system.

## Installation

Download:

    SystemStatus-Windows-Setup-1.0.0.exe

Run the installer normally.

System Status installs for the current Windows user and does not require an
administrator-level system installation.

The installer can optionally create a desktop shortcut and configure System
Status to start automatically with Windows.

Python, PowerShell, and a separate LibreHardwareMonitor installation are not
required by users of the packaged release.

## Controls

Right-click the System Status widget to access its controls and settings.

The widget can be moved around the desktop when unlocked. Its position is
saved between launches.

## Network status

System Status distinguishes normal internet connectivity from recognized VPN
tunnels.

Status colors:

- Blue - ONLINE
- Green - SECURE
- Red - OFFLINE

Live download and upload rates are displayed in green.

## Temperatures

System Status uses LibreHardwareMonitor components for supported Windows
hardware temperature sensors.

CPU and GPU temperature availability depends on the hardware, firmware,
drivers, and sensor accessibility of the individual PC.

## Source layout

    backend/       Windows telemetry collectors
    ui/            Windows desktop interface and settings
    runtime/       Bundled LibreHardwareMonitor runtime dependencies
    installer/     Windows installer definition
    licenses/      Third-party license material

The Linux/KDE Plasma implementation remains separate under `linux/`.

## Third-party software

The Windows distribution includes components from LibreHardwareMonitor.

Applicable licensing and third-party notices are provided under:

    windows/licenses/LibreHardwareMonitor/

and:

    windows/THIRD-PARTY-NOTICES.md

## License

System Status is released under the MIT License.

See the repository `LICENSE` file for the full license text.

## Maintainer

**The Fat Pirate**
