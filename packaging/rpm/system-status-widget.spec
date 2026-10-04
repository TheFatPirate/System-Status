Name: system-status-widget
Version:        1.0.0
Release: 1%{?dist}
Summary: Plasma 6 hardware and VPN-aware system status widget

License: MIT
Source0: system-status-source-1.0.0.tar.gz

BuildRequires: cmake
BuildRequires: gcc-c++
BuildRequires: ninja-build
BuildRequires: systemd-rpm-macros
BuildRequires: qt6-qtbase-devel
BuildRequires: qt6-qtdeclarative-devel

Requires: python3
Requires: NetworkManager

%description
System Status is a Plasma 6 desktop widget providing live hardware,
storage, display, gaming, and network telemetry.

Network security status is VPN-aware and currently targets Proton VPN
WireGuard connections. SECURE indicates the expected VPN connection is
active. OFFLINE indicates the expected VPN connection is not active and
does not necessarily mean that the computer has lost internet connectivity.

Optional tools such as smartctl, kscreen-doctor, MangoHud, and GameMode
provide additional telemetry when available but are not required.

%prep
%setup -q -c -T
tar -xzf %{SOURCE0}

test -f metadata.json
test -f contents/ui/main.qml
test -f backend/qml-plugin/CMakeLists.txt
test -x backend/status/system-statusd-v2
test -x backend/status/system-status-sessiond-v2

%build
%cmake -S backend/qml-plugin -B %{__cmake_builddir} -G Ninja
%cmake_build

%install
rm -rf %{buildroot}

mkdir -p %{buildroot}%{_libdir}/qt6/qml/org/systemstatus/private/status
mkdir -p %{buildroot}%{_datadir}/plasma/plasmoids/com.systemstatus.widget

cp -a %{__cmake_builddir}/qml/org/systemstatus/private/status/. %{buildroot}%{_libdir}/qt6/qml/org/systemstatus/private/status/

cp -a metadata.json contents %{buildroot}%{_datadir}/plasma/plasmoids/com.systemstatus.widget/

mkdir -p %{buildroot}%{_libexecdir}/system-status/status/providers
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_userunitdir}
mkdir -p %{buildroot}%{_prefix}/lib/systemd/system-preset
mkdir -p %{buildroot}%{_prefix}/lib/systemd/user-preset

cp -a backend/status/*.py %{buildroot}%{_libexecdir}/system-status/status/
cp -a backend/status/providers/*.py %{buildroot}%{_libexecdir}/system-status/status/providers/

install -m 0755 backend/status/system-statusd-v2 %{buildroot}%{_libexecdir}/system-status/status/system-statusd-v2
install -m 0755 backend/status/system-status-sessiond-v2 %{buildroot}%{_libexecdir}/system-status/status/system-status-sessiond-v2

install -m 0644 packaging/systemd/system/system-status-v2.service %{buildroot}%{_unitdir}/system-status-v2.service
install -m 0644 packaging/systemd/system-preset/90-system-status.preset %{buildroot}%{_prefix}/lib/systemd/system-preset/90-system-status.preset
install -m 0644 packaging/systemd/user/system-status-session-v2.service %{buildroot}%{_userunitdir}/system-status-session-v2.service
install -m 0644 packaging/systemd/user-preset/90-system-status.preset %{buildroot}%{_prefix}/lib/systemd/user-preset/90-system-status.preset

%post
%systemd_post system-status-v2.service
%systemd_user_post system-status-session-v2.service

%preun
%systemd_preun system-status-v2.service
%systemd_user_preun system-status-session-v2.service

%postun
%systemd_postun_with_restart system-status-v2.service
%systemd_user_postun_with_restart system-status-session-v2.service

%files
%{_datadir}/plasma/plasmoids/com.systemstatus.widget/
%{_libdir}/qt6/qml/org/systemstatus/private/status/
%{_libexecdir}/system-status/
%{_unitdir}/system-status-v2.service
%{_prefix}/lib/systemd/system-preset/90-system-status.preset
%{_userunitdir}/system-status-session-v2.service
%{_prefix}/lib/systemd/user-preset/90-system-status.preset

%changelog
* Sun Oct 04 2026 The Fat Pirate <thefatpirate@users.noreply.github.com> - 1.0.0-1
- Initial public release of System Status.
- Added Plasma 6 hardware, storage, display, gaming, and network telemetry.
- Added VPN-aware SECURE/OFFLINE network status for Proton VPN WireGuard.
