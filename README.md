# System Status

**System Status** is a lightweight desktop system-monitoring project by
**The Fat Pirate**, available for Windows and Linux.

System Status provides at-a-glance information about system resources,
hardware, storage, temperatures, network activity, and system state.

## Downloads

### Windows 1.0.0

Windows users should download:

    SystemStatus-Windows-Setup-1.0.0.exe

The Windows installer provides a normal desktop installation and does not
require Python, PowerShell, or LibreHardwareMonitor to be installed separately.

Windows features include:

- CPU usage and temperature
- RAM usage
- GPU usage and temperature
- Per-drive or combined storage monitoring
- Live network upload and download activity
- Network connection state
- Configurable warning and critical thresholds
- Configurable widget layout
- Optional desktop shortcut
- Optional automatic startup with Windows
- Lockable and movable desktop widget

See `windows/README.md` for Windows-specific information.

### Linux 1.0.0

The Linux version is a KDE Plasma 6 desktop widget.

The current Linux release is built and validated for Fedora 44 x86_64 with
KDE Plasma 6.

Linux release package:

    system-status-widget-1.0.0-1.fc44.x86_64.rpm

The Linux implementation includes system and session telemetry services and
integrates directly with KDE Plasma.

See the `main` branch README for Linux installation, telemetry, service, and
configuration information.

## Platform layout

    main        Linux / KDE Plasma implementation (default branch)
    windows/    Windows implementation

The two implementations share the System Status project name and release
version while using platform-specific backends and interfaces.

## License

System Status is released under the MIT License.

See `LICENSE` for the full license text.

The Windows distribution includes LibreHardwareMonitor components under their
applicable licenses. Third-party notices are included with the Windows source
and installed application.

## Maintainer

**The Fat Pirate**
