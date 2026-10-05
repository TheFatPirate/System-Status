import QtQuick

import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents

import org.systemstatus.private.status 1.0


PlasmoidItem {
    id: root

    Plasmoid.backgroundHints:
        PlasmaCore.Types.NoBackground

    implicitWidth: 270
    implicitHeight: 120

    property var sensors: ({})

    SnapshotReader {
        id: snapshotReader
    }

    function parseSensors(text) {
        if (!text || text.length === 0)
            return {}

        try {
            return JSON.parse(text).sensors || {}
        } catch (error) {
            return {}
        }
    }

    function refresh() {
        var merged = {}

        var system =
            parseSensors(
                snapshotReader.readFile(
                    "/run/system-status/status-v2/status.json"
                )
            )

        var session = {}

        var runtime =
            snapshotReader.runtimeDir()

        if (runtime.length > 0) {
            session =
                parseSensors(
                    snapshotReader.readFile(
                        runtime
                        + "/system-status/status-v2-session/status.json"
                    )
                )
        }

        var key

        for (key in system)
            merged[key] = system[key]

        for (key in session)
            merged[key] = session[key]

        sensors = merged
    }

    function sensor(id) {
        return sensors[id] || null
    }

    function value(id, fallback) {
        var item = sensor(id)

        if (
            !item
            || item.value === undefined
            || item.value === null
        )
            return fallback

        return item.value
    }

    function percentage(id) {
        var number =
            Number(value(id, 0))

        if (!isFinite(number))
            number = 0

        return number.toFixed(1) + "%"
    }

    function safeSetting(value, fallback) {
        var number = Number(value)

        if (!isFinite(number) || number <= 0)
            return fallback

        return number
    }

    function usageWarning() {
        return safeSetting(
            Plasmoid.configuration.usageWarning,
            75
        )
    }

    function usageCritical() {
        return safeSetting(
            Plasmoid.configuration.usageCritical,
            90
        )
    }

    function cpuWarning() {
        return safeSetting(
            Plasmoid.configuration.cpuTempWarning,
            80
        )
    }

    function cpuCritical() {
        return safeSetting(
            Plasmoid.configuration.cpuTempCritical,
            90
        )
    }

    function gpuWarning() {
        return safeSetting(
            Plasmoid.configuration.gpuTempWarning,
            85
        )
    }

    function gpuCritical() {
        return safeSetting(
            Plasmoid.configuration.gpuTempCritical,
            95
        )
    }

    function findCpuTemperature() {
        var packages = []

        /*
         * Prefer package-level sensors, but never
         * assume package 0 exists or is the only CPU.
         */
        for (var id in sensors) {
            var match =
                id.match(
                    /^cpu\.package\.([0-9]+)\.temperature$/
                )

            if (
                match
                && sensors[id].available !== false
            ) {
                packages.push(
                    {
                        index:
                            Number(match[1]),
                        sensor:
                            sensors[id]
                    }
                )
            }
        }

        packages.sort(
            function(a, b) {
                return a.index - b.index
            }
        )

        if (packages.length > 0)
            return packages[0].sensor

        /*
         * Fall back to any CPU temperature the
         * provider exposes. This also handles
         * unusual or future sensor layouts.
         */
        var candidates = []

        for (var sensorId in sensors) {
            if (
                /^cpu\..+\.temperature$/
                    .test(sensorId)
                && sensors[sensorId]
                    .available !== false
            ) {
                candidates.push(
                    sensorId
                )
            }
        }

        candidates.sort()

        if (candidates.length > 0)
            return sensors[
                candidates[0]
            ]

        return null
    }


    function automaticGpuPrefix() {
        var indexes = []

        for (var id in sensors) {
            var match =
                id.match(
                    /^gpu\.([0-9]+)\.usage$/
                )

            if (
                match
                && sensors[id].available !== false
            ) {
                indexes.push(
                    Number(match[1])
                )
            }
        }

        if (indexes.length === 0) {
            /*
             * Some future providers may expose useful
             * telemetry without a usage sensor. Fall
             * back to any discovered gpu.N namespace.
             */
            for (var fallbackId in sensors) {
                var fallbackMatch =
                    fallbackId.match(
                        /^gpu\.([0-9]+)\./
                    )

                if (
                    fallbackMatch
                    && sensors[fallbackId]
                        .available !== false
                ) {
                    indexes.push(
                        Number(
                            fallbackMatch[1]
                        )
                    )
                }
            }
        }

        if (indexes.length === 0)
            return ""

        indexes.sort(
            function(a, b) {
                return a - b
            }
        )

        return "gpu." + indexes[0]
    }



    function primaryGpuPrefix() {
        var configured =
            String(
                Plasmoid.configuration.gpuDevice
                || "auto"
            )

        if (
            configured !== "auto"
            && configured.length > 0
        ) {
            /*
             * A manual selection is only honored while
             * that GPU actually exists. Hot removal,
             * driver failure, etc. falls back to Auto.
             */
            var prefix =
                configured.indexOf("gpu.") === 0
                    ? configured
                    : "gpu." + configured

            for (var id in sensors) {
                if (
                    id.indexOf(
                        prefix + "."
                    ) === 0
                    && sensors[id].available !== false
                ) {
                    return prefix
                }
            }
        }

        return root.automaticGpuPrefix()
    }

    function findGpuTemperature() {
        var prefix =
            root.primaryGpuPrefix()

        if (!prefix)
            return null

        /*
         * Edge is the preferred AMD sensor when present.
         * Other providers/hardware can expose another
         * temperature under the same gpu.N namespace.
         */
        var preferred =
            sensor(
                prefix
                + ".temperature.edge"
            )

        if (
            preferred
            && preferred.available !== false
        )
            return preferred

        var temperaturePrefix =
            prefix + ".temperature."

        for (var id in sensors) {
            if (
                id.indexOf(
                    temperaturePrefix
                ) === 0
                && sensors[id].available !== false
            )
                return sensors[id]
        }

        return null
    }


    function temperatureC(item) {
        if (!item)
            return -1

        var number =
            Number(item.value)

        return isFinite(number)
            ? number
            : -1
    }

    function temperatureText(item) {
        var c =
            temperatureC(item)

        if (c < 0)
            return ""

        if (
            Plasmoid.configuration.temperatureUnit
            === "F"
        ) {
            return (
                c * 9 / 5 + 32
            ).toFixed(0) + " °F"
        }

        return c.toFixed(0) + " °C"
    }

    function version() {
        return String(
            value("system.version", "?")
        )
    }

    function networkState() {
        return String(
            value("network.security", "OFFLINE")
        ).trim().toUpperCase()
    }

    function networkColor() {
        var state =
            networkState()

        if (state === "SECURE")
            return "#39ff14"

        if (state === "OFFLINE")
            return "#ff3030"

        return "white"
    }

    Component.onCompleted:
        refresh()

    Timer {
        interval: Math.max(
            250,
            safeSetting(
                Plasmoid.configuration.refreshMs,
                500
            )
        )

        running: true
        repeat: true

        onTriggered:
            root.refresh()
    }



    function sensorNumber(id) {
        var n = Number(
            root.value(id, NaN)
        )

        return isFinite(n)
            ? n
            : NaN
    }


    function appendExtra(parts, text) {
        if (
            text !== undefined
            && text !== null
            && String(text).length > 0
        ) {
            parts.push(String(text))
        }
    }


    function bytesText(value) {
        var n = Number(value)

        if (!isFinite(n) || n < 0)
            return ""

        var units = [
            "B",
            "KB",
            "MB",
            "GB",
            "TB"
        ]

        var index = 0

        while (
            n >= 1024
            && index < units.length - 1
        ) {
            n /= 1024
            index += 1
        }

        var digits =
            index >= 3
            ? 1
            : 0

        return n.toFixed(digits)
            + " "
            + units[index]
    }


    function cpuFrequencyText() {
        var total = 0
        var count = 0

        for (var id in sensors) {
            if (
                /^cpu\.core\.[0-9]+\.frequency$/
                    .test(id)
                && sensors[id].available !== false
            ) {
                var frequency =
                    Number(
                        sensors[id].value
                    )

                if (isFinite(frequency)) {
                    total += frequency
                    count += 1
                }
            }
        }

        if (count === 0)
            return ""

        /*
         * CPU provider publishes MHz.
         */
        var average =
            total / count

        if (average >= 1000) {
            return (
                average / 1000
            ).toFixed(2)
                + " GHz"
        }

        return Math.round(average)
            + " MHz"
    }


    function ramUsedTotalText() {
        var used =
            root.sensorNumber(
                "memory.ram.used"
            )

        var total =
            root.sensorNumber(
                "memory.ram.total"
            )

        if (
            !isFinite(used)
            || !isFinite(total)
        )
            return ""

        return root.bytesText(used)
            + " / "
            + root.bytesText(total)
    }


    function ramAvailableText() {
        var value =
            root.sensorNumber(
                "memory.ram.available"
            )

        if (value === null)
            return ""

        return "AVAIL "
            + root.bytesText(value)
    }

    function ramFreeText() {
        var value =
            root.sensorNumber(
                "memory.ram.free"
            )

        if (value === null)
            return ""

        return "FREE "
            + root.bytesText(value)
    }

    function swapUsedTotalText() {
        var used =
            root.sensorNumber(
                "memory.swap.used"
            )

        var total =
            root.sensorNumber(
                "memory.swap.total"
            )

        if (
            used === null
            || total === null
        )
            return ""

        return "SWAP "
            + root.bytesText(used)
            + "/"
            + root.bytesText(total)
    }

    function swapUsageText() {
        var used =
            root.sensorNumber(
                "memory.swap.used"
            )

        var total =
            root.sensorNumber(
                "memory.swap.total"
            )

        if (
            used === null
            || total === null
            || total <= 0
        )
            return ""

        var usage =
            used / total * 100

        return "SWAP "
            + usage.toFixed(1)
            + "%"
    }


    function gpuFanRpmText() {
        var value =
            root.sensorNumber(
                root.primaryGpuPrefix()
                + ".fan.rpm"
            )

        if (!isFinite(value))
            return ""

        return Math.round(value)
            + " RPM"
    }


    function gpuFanPercentText() {
        var value =
            root.sensorNumber(
                root.primaryGpuPrefix()
                + ".fan.percent"
            )

        if (!isFinite(value))
            return ""

        return Math.round(value)
            + "%"
    }


    function gpuClockText(id) {
        var value =
            root.sensorNumber(id)

        if (!isFinite(value))
            return ""

        if (value > 10000000)
            value /= 1000000
        else if (value > 10000)
            value /= 1000

        return Math.round(value)
            + " MHz"
    }


    function gpuPowerText() {
        var value =
            root.sensorNumber(
                root.primaryGpuPrefix()
                + ".power"
            )

        if (!isFinite(value))
            return ""

        return value.toFixed(1)
            + " W"
    }


    function gpuVoltageText() {
        var value =
            root.sensorNumber(
                root.primaryGpuPrefix()
                + ".voltage"
            )

        if (!isFinite(value))
            return ""

        if (value > 20)
            value /= 1000

        return value.toFixed(2)
            + " V"
    }


    function gpuVramText() {
        var used =
            root.sensorNumber(
                root.primaryGpuPrefix()
                + ".vram.used"
            )

        var total =
            root.sensorNumber(
                root.primaryGpuPrefix()
                + ".vram.total"
            )

        if (
            !isFinite(used)
            || !isFinite(total)
        )
            return ""

        return root.bytesText(used)
            + " / "
            + root.bytesText(total)
    }


    function rateText(value) {
        var n = Number(value)

        if (!isFinite(n) || n < 0)
            return ""

        var units = [
            "B/s",
            "KB/s",
            "MB/s",
            "GB/s"
        ]

        var index = 0

        while (
            n >= 1024
            && index < units.length - 1
        ) {
            n /= 1024
            index += 1
        }

        return n.toFixed(
            index >= 2 ? 1 : 0
        ) + " " + units[index]
    }


    function storagePrefix() {
        var configured =
            String(
                Plasmoid.configuration.storageTarget
                || "storage.root"
            )

        /*
         * Only accept a selected target if its usage
         * sensor currently exists. A removed/unmounted
         * filesystem safely falls back to root.
         */
        if (
            configured.length > 0
            && root.sensor(
                configured + ".usage"
            )
        ) {
            return configured
        }

        if (
            root.sensor(
                "storage.root.usage"
            )
        ) {
            return "storage.root"
        }

        /*
         * Extreme fallback for unusual systems where
         * root telemetry is unavailable.
         */
        for (var id in sensors) {
            if (
                /^storage\.mount\..+\.usage$/
                    .test(id)
                && sensors[id].available !== false
            ) {
                return id.substring(
                    0,
                    id.length - 6
                )
            }
        }

        return ""
    }


    function storageExtraText() {
        var parts = []
        var prefix =
            root.storagePrefix()

        if (!prefix)
            return ""

        if (
            Plasmoid.configuration
                .showStorageUsedAvailable
        ) {
            var used =
                root.sensorNumber(
                    prefix + ".used"
                )

            var available =
                root.sensorNumber(
                    prefix + ".available"
                )

            if (
                isFinite(used)
                && isFinite(available)
            ) {
                root.appendExtra(
                    parts,
                    root.bytesText(used)
                    + " / "
                    + root.bytesText(available)
                )
            }
        }

        if (
            Plasmoid.configuration
                .showStorageFilesystem
        ) {
            root.appendExtra(
                parts,
                root.value(
                    prefix + ".filesystem",
                    ""
                )
            )
        }

        return parts.join("   ")
    }


    function networkInterfaceNames() {
        var names = ({})
        var result = []

        for (var id in sensors) {
            var match =
                id.match(
                    /^network\.(.+)\.rx\.rate$/
                )

            if (
                match
                && sensors[id].available !== false
            ) {
                names[match[1]] = true
            }
        }

        for (var name in names)
            result.push(name)

        result.sort()

        return result
    }


    function looksLikeTunnel(name) {
        var lower =
            String(name).toLowerCase()

        return (
            lower.indexOf("proton") >= 0
            || lower.indexOf("vpn") >= 0
            || lower.indexOf("tun") === 0
            || lower.indexOf("tap") === 0
            || lower.indexOf("wg") === 0
            || lower.indexOf("tailscale") >= 0
            || lower.indexOf("pvpn") >= 0
        )
    }


    function automaticNetworkPrefix() {
        var names =
            root.networkInterfaceNames()

        if (names.length === 0)
            return ""

        /*
         * A link-speed sensor strongly indicates a
         * physical Ethernet/Wi-Fi style interface.
         */
        for (
            var i = 0;
            i < names.length;
            ++i
        ) {
            var prefix =
                "network." + names[i]

            if (
                root.sensor(
                    prefix + ".link.speed"
                )
            ) {
                return prefix
            }
        }

        /*
         * Next prefer a non-tunnel interface.
         */
        for (
            var j = 0;
            j < names.length;
            ++j
        ) {
            if (
                !root.looksLikeTunnel(
                    names[j]
                )
            ) {
                return (
                    "network."
                    + names[j]
                )
            }
        }

        /*
         * Last resort: use whatever telemetry exists.
         */
        return (
            "network."
            + names[0]
        )
    }



    function primaryNetworkPrefix() {
        var configured =
            String(
                Plasmoid.configuration.networkDevice
                || "auto"
            )

        if (
            configured !== "auto"
            && configured.length > 0
        ) {
            var name =
                configured.indexOf("network.") === 0
                    ? configured.substring(8)
                    : configured

            var prefix =
                "network." + name

            if (
                root.sensor(
                    prefix + ".rx.rate"
                )
                || root.sensor(
                    prefix + ".tx.rate"
                )
            ) {
                return prefix
            }
        }

        return root.automaticNetworkPrefix()
    }

    function networkExtraText() {
        var parts = []
        var prefix =
            root.primaryNetworkPrefix()

        if (!prefix)
            return ""

        if (
            Plasmoid.configuration
                .showNetworkRx
        ) {
            var rx =
                root.sensorNumber(
                    prefix + ".rx.rate"
                )

            if (isFinite(rx)) {
                root.appendExtra(
                    parts,
                    "↓ "
                    + root.rateText(rx)
                )
            }
        }

        if (
            Plasmoid.configuration
                .showNetworkTx
        ) {
            var tx =
                root.sensorNumber(
                    prefix + ".tx.rate"
                )

            if (isFinite(tx)) {
                root.appendExtra(
                    parts,
                    "↑ "
                    + root.rateText(tx)
                )
            }
        }

        if (
            Plasmoid.configuration
                .showNetworkLinkSpeed
        ) {
            var speed =
                root.value(
                    prefix + ".link.speed",
                    ""
                )

            root.appendExtra(
                parts,
                speed
            )
        }

        return parts.join("   ")
    }



    function networkFooterText() {
        var extra =
            root.networkExtraText()

        return extra.length > 0
            ? "   " + extra
            : ""
    }



    function gamingExtraText() {
        var parts = []

        if (
            !root.value(
                "gaming.active",
                false
            )
        ) {
            return ""
        }

        if (
            Plasmoid.configuration
                .showGamingFps
        ) {
            var fps =
                root.sensorNumber(
                    "gaming.fps"
                )

            if (isFinite(fps)) {
                root.appendExtra(
                    parts,
                    Math.round(fps)
                    + " FPS"
                )
            }
        }

        if (
            Plasmoid.configuration
                .showGamingFrametime
        ) {
            var ft =
                root.sensorNumber(
                    "gaming.frametime"
                )

            if (isFinite(ft)) {
                root.appendExtra(
                    parts,
                    ft.toFixed(1)
                    + " ms"
                )
            }
        }

        if (
            Plasmoid.configuration
                .showGamingAverageFps
        ) {
            var avg =
                root.sensorNumber(
                    "gaming.fps.average"
                )

            if (isFinite(avg)) {
                root.appendExtra(
                    parts,
                    "AVG "
                    + Math.round(avg)
                )
            }
        }

        if (
            Plasmoid.configuration
                .showGamingOneLow
        ) {
            var low =
                root.sensorNumber(
                    "gaming.fps.1low"
                )

            if (isFinite(low)) {
                root.appendExtra(
                    parts,
                    "1% "
                    + Math.round(low)
                )
            }
        }

        if (
            Plasmoid.configuration
                .showGamingPointOneLow
        ) {
            var pointLow =
                root.sensorNumber(
                    "gaming.fps.01low"
                )

            if (isFinite(pointLow)) {
                root.appendExtra(
                    parts,
                    "0.1% "
                    + Math.round(pointLow)
                )
            }
        }

        return parts.join("   ")
    }



    function cpuExtraText() {
        var parts = []

        if (
            Plasmoid.configuration
                .showCpuTemperature
        ) {
            root.appendExtra(
                parts,
                root.temperatureText(
                    root.findCpuTemperature()
                )
            )
        }

        if (
            Plasmoid.configuration
                .showCpuFrequency
        ) {
            root.appendExtra(
                parts,
                root.cpuFrequencyText()
            )
        }

        return parts.join("   ")
    }


    function ramExtraText() {
        var parts = []

        if (
            Plasmoid.configuration
                .showRamUsedTotal
        ) {
            root.appendExtra(
                parts,
                root.ramUsedTotalText()
            )
        }

        if (
            Plasmoid.configuration
                .showRamAvailable
        ) {
            root.appendExtra(
                parts,
                root.ramAvailableText()
            )
        }

        if (
            Plasmoid.configuration
                .showRamFree
        ) {
            root.appendExtra(
                parts,
                root.ramFreeText()
            )
        }

        if (
            Plasmoid.configuration
                .showSwapUsedTotal
        ) {
            root.appendExtra(
                parts,
                root.swapUsedTotalText()
            )
        }

        if (
            Plasmoid.configuration
                .showSwapUsage
        ) {
            root.appendExtra(
                parts,
                root.swapUsageText()
            )
        }

        return parts.join("   ")
    }


    function gpuExtraText() {
        var parts = []

        if (
            Plasmoid.configuration
                .showGpuTemperature
        ) {
            root.appendExtra(
                parts,
                root.temperatureText(
                    root.findGpuTemperature()
                )
            )
        }

        if (
            Plasmoid.configuration
                .showGpuFanRpm
        ) {
            root.appendExtra(
                parts,
                root.gpuFanRpmText()
            )
        }

        if (
            Plasmoid.configuration
                .showGpuFanPercent
        ) {
            root.appendExtra(
                parts,
                root.gpuFanPercentText()
            )
        }

        if (
            Plasmoid.configuration
                .showGpuCoreClock
        ) {
            root.appendExtra(
                parts,
                root.gpuClockText(
                    root.primaryGpuPrefix()
                    + ".clock.core"
                )
            )
        }

        if (
            Plasmoid.configuration
                .showGpuMemoryClock
        ) {
            root.appendExtra(
                parts,
                root.gpuClockText(
                    root.primaryGpuPrefix()
                    + ".clock.memory"
                )
            )
        }

        if (
            Plasmoid.configuration
                .showGpuPower
        ) {
            root.appendExtra(
                parts,
                root.gpuPowerText()
            )
        }

        if (
            Plasmoid.configuration
                .showGpuVoltage
        ) {
            root.appendExtra(
                parts,
                root.gpuVoltageText()
            )
        }

        if (
            Plasmoid.configuration
                .showGpuVram
        ) {
            root.appendExtra(
                parts,
                root.gpuVramText()
            )
        }

        root.appendExtra(
            parts,
            root.gamingExtraText()
        )

        return parts.join("   ")
    }


    StatusRow {
        id: cpuRow

        anchors.left: parent.left
        anchors.right: parent.right
        y: 0

        label: "CPU"

        usage:
            root.percentage(
                "cpu.total.usage"
            )

        numericUsage:
            Number(
                root.value(
                    "cpu.total.usage",
                    0
                )
            )

        numericTemperature:
            root.temperatureC(
                root.findCpuTemperature()
            )

        warningTemperature:
            root.cpuWarning()

        criticalTemperature:
            root.cpuCritical()

        extra:
            root.cpuExtraText()
    }


    StatusRow {
        id: ramRow

        anchors.left: parent.left
        anchors.right: parent.right
        y: 22

        label: "RAM"

        usage:
            root.percentage(
                "memory.ram.usage"
            )

        numericUsage:
            Number(
                root.value(
                    "memory.ram.usage",
                    0
                )
            )

        extra:
            root.ramExtraText()
    }


    StatusRow {
        id: gpuRow

        anchors.left: parent.left
        anchors.right: parent.right
        y: 44

        label: "GPU"

        usage:
            root.percentage(
                root.primaryGpuPrefix()
                + ".usage"
            )

        numericUsage:
            Number(
                root.value(
                    root.primaryGpuPrefix()
                    + ".usage",
                    0
                )
            )

        numericTemperature:
            root.temperatureC(
                root.findGpuTemperature()
            )

        warningTemperature:
            root.gpuWarning()

        criticalTemperature:
            root.gpuCritical()

        extra:
            root.gpuExtraText()
    }


    StatusRow {
        id: storageRow

        anchors.left: parent.left
        anchors.right: parent.right
        y: 66

        label: "STORAGE"

        usage:
            root.percentage(
                root.storagePrefix()
                + ".usage"
            )

        numericUsage:
            Number(
                root.value(
                    root.storagePrefix()
                    + ".usage",
                    0
                )
            )

        extra:
            root.storageExtraText()
    }


    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right

        y: 89
        height: 1

        color: "white"
        opacity: 0.85
    }


    Item {
        anchors.left: parent.left
        anchors.right: parent.right

        y: 94
        height: 22

        PlasmaComponents.Label {
            id: systemLabel

            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter

            text: "SYSTEM // NETWORK:"

            font.bold: true
            font.pixelSize: 14

            color: "white"
        }

        PlasmaComponents.Label {
            anchors.left:
                systemLabel.right

            anchors.leftMargin: 5

            anchors.verticalCenter:
                parent.verticalCenter

            text:
                root.networkState()
                + root.networkFooterText()

            font.bold: true
            font.pixelSize: 14

            color:
                root.networkColor()
        }
    }


    component StatusRow: Item {
        id: row

        property string label: ""
        property string usage: ""
        property string extra: ""

        property real numericUsage: 0
        property real numericTemperature: -1

        property real warningTemperature: 999
        property real criticalTemperature: 999

        readonly property bool usageWarning:
            numericUsage
            >= root.usageWarning()

        readonly property bool usageCritical:
            numericUsage
            >= root.usageCritical()

        readonly property bool temperatureWarning:
            numericTemperature >= 0
            && numericTemperature
               >= warningTemperature

        readonly property bool temperatureCritical:
            numericTemperature >= 0
            && numericTemperature
               >= criticalTemperature

        readonly property bool warningActive:
            usageWarning
            || temperatureWarning

        readonly property bool criticalActive:
            usageCritical
            || temperatureCritical

        readonly property color alarmColor:
            criticalActive
            ? (
                Plasmoid.configuration.criticalColor
                || "#ff3030"
              )
            : warningActive
              ? (
                    Plasmoid.configuration.warningColor
                    || "#ff9d00"
                )
              : "white"

        property real pulseOpacity: 1.0

        height: 22

        opacity:
            warningActive
            ? pulseOpacity
            : 1.0

        SequentialAnimation on pulseOpacity {
            running:
                row.warningActive

            loops:
                Animation.Infinite

            NumberAnimation {
                from: 1.0
                to: 0.35

                duration:
                    row.criticalActive
                    ? 300
                    : 650
            }

            NumberAnimation {
                from: 0.35
                to: 1.0

                duration:
                    row.criticalActive
                    ? 300
                    : 650
            }
        }

        PlasmaComponents.Label {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter

            width: 72

            text:
                row.label

            font.bold: true
            font.pixelSize: 14

            color:
                row.alarmColor
        }

        PlasmaComponents.Label {
            anchors.left: parent.left
            anchors.leftMargin: 78

            anchors.verticalCenter:
                parent.verticalCenter

            width: 54

            horizontalAlignment:
                Text.AlignRight

            text:
                row.usage

            font.bold: true
            font.pixelSize: 14

            color:
                row.alarmColor
        }

        PlasmaComponents.Label {
            anchors.left: parent.left
            anchors.leftMargin: 142

            anchors.verticalCenter:
                parent.verticalCenter

            text:
                row.extra

            font.bold: true
            font.pixelSize: 14

            color:
                row.alarmColor

            visible:
                row.extra.length > 0
        }
    }
}
