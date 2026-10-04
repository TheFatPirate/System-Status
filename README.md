# System Status

**System Status** is a KDE Plasma 6 desktop system-monitoring widget by **The Fat Pirate**.

It provides an at-a-glance view of hardware, resource usage, temperatures,
storage, display information, gaming telemetry, network activity, and
VPN-aware network security state.

## Features

System Status can expose telemetry including:

- CPU usage, frequency, and temperature
- RAM and swap usage
- Storage usage and available storage information
- Display resolution, refresh rate, brightness, HDR, VRR, and scale
- Network receive and transmit activity
- Network link speed
- VPN security state
- GameMode availability and state
- MangoHud availability and gaming telemetry when available

Sensor availability depends on the hardware, drivers, desktop session, and
optional utilities installed on the system.

## VPN security indicator

The network security indicator is intentionally VPN-aware.

System Status 1.0.0 currently expects a Proton VPN WireGuard interface named:

    proton0

When NetworkManager reports the expected Proton VPN WireGuard connection as
active, the widget displays:

    SECURE

When the expected VPN connection is not active, it displays:

    OFFLINE

`OFFLINE` refers to the expected VPN security state. It does **not**
necessarily mean the computer has lost ordinary internet connectivity.

### Status colors

- Green — `SECURE`
- Red — `OFFLINE`

Hardware sensors retain their own warning and critical color behavior.

## Requirements

Core requirements:

- KDE Plasma 6
- Qt 6 / QML
- NetworkManager
- Python 3

Optional tools can provide additional telemetry when available, including:

- `smartctl`
- `kscreen-doctor`
- MangoHud
- GameMode

These optional tools are not required for the core widget to operate.

## Fedora 44 RPM

System Status 1.0.0 has been built and validated on:

- Fedora 44 x86_64
- KDE Plasma 6

Install the binary RPM with:

    sudo dnf install ./system-status-widget-1.0.0-1.fc44.x86_64.rpm

The package installs and enables two telemetry services:

    system-status-v2.service
    system-status-session-v2.service

The system service collects hardware and network telemetry.

The user-session service collects session-specific information such as display
and gaming telemetry.

After installation, the widget is available in Plasma as:

    System Status

Add it to the desktop through Plasma's normal **Add Widgets** interface.

## Verify services

The system service can be checked with:

    systemctl status system-status-v2.service

The session service can be checked with:

    systemctl --user status system-status-session-v2.service

Both should normally be enabled. They are configured to start automatically
for the appropriate system or graphical-session target.

## Runtime telemetry

System telemetry is written to:

    /run/system-status/status-v2/status.json

Session telemetry is written beneath the current user's runtime directory:

    $XDG_RUNTIME_DIR/system-status/status-v2-session/status.json

These files use JSON and are consumed by the Plasma widget through the
System Status QML integration.

## Release verification

The release directory includes a `SHA256SUMS` file.

Verify release artifacts with:

    sha256sum -c SHA256SUMS

## License

System Status is released under the MIT License.

See `LICENSE` for the full license text.

## Author

**The Fat Pirate**
