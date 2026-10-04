import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

import org.systemstatus.private.status 1.0

KCM.SimpleKCM {
    id: root

    property string cfg_gpuDevice: "auto"
    property string cfg_networkDevice: "auto"
    property string cfg_storageTarget: "storage.root"
    property string cfg_storageDevice: "auto"


    property var gpuDeviceModel: []
    property var networkDeviceModel: []
    property var storageTargetModel: []
    property var storageDeviceModel: []

    SnapshotReader {
        id: snapshotReader
    }

    function parseSensors(text) {
        if (!text || text.length === 0)
            return ({})

        try {
            return JSON.parse(text).sensors || ({})
        } catch (error) {
            return ({})
        }
    }

    function mergedSensors() {
        var merged = ({})

        var system =
            root.parseSensors(
                snapshotReader.readFile(
                    "/run/system-status/status-v2/status.json"
                )
            )

        var runtime =
            snapshotReader.runtimeDir()

        var session = ({})

        if (runtime.length > 0) {
            session =
                root.parseSensors(
                    snapshotReader.readFile(
                        runtime
                        + "/system-status/status-v2-session/status.json"
                    )
                )
        }

        var id

        for (id in system)
            merged[id] = system[id]

        for (id in session)
            merged[id] = session[id]

        return merged
    }

    function rebuildDeviceModels() {
        var sensors =
            root.mergedSensors()

        var gpuIndexes = ({})
        var interfaces = ({})
        var storageTargets = ({})
        var storageDevices = ({})

        var id

        for (id in sensors) {
            var item = sensors[id]

            if (
                item
                && item.available === false
            )
                continue

            var gpuMatch =
                id.match(
                    /^gpu\.([0-9]+)\./
                )

            if (gpuMatch)
                gpuIndexes[gpuMatch[1]] = true

            var networkMatch =
                id.match(
                    /^network\.(.+)\.rx\.rate$/
                )

            if (networkMatch)
                interfaces[networkMatch[1]] = true


            if (
                id === "storage.root.usage"
            ) {
                storageTargets[
                    "storage.root"
                ] = "/"
            }

            var mountMatch =
                id.match(
                    /^storage\.mount\.(.+)\.usage$/
                )

            if (mountMatch) {
                storageTargets[
                    "storage.mount."
                    + mountMatch[1]
                ] =
                    "/"
                    + mountMatch[1]
                        .replace(/\./g, "/")
                        .replace(/_/g, " ")
            }


            var driveMatch =
                id.match(
                    /^storage\.([^.]+)\.(.+)$/
                )

            if (
                driveMatch
                && driveMatch[1] !== "root"
                && driveMatch[1] !== "mount"
            ) {
                var driveName =
                    driveMatch[1]

                storageDevices[
                    driveName
                ] = true
            }
        }

        var gpuNumbers = []

        for (var gpu in gpuIndexes)
            gpuNumbers.push(Number(gpu))

        gpuNumbers.sort(
            function(a, b) {
                return a - b
            }
        )

        var gpuModel = [
            {
                text: i18n("Automatic"),
                value: "auto"
            }
        ]

        for (
            var g = 0;
            g < gpuNumbers.length;
            ++g
        ) {
            var index = gpuNumbers[g]

            gpuModel.push(
                {
                    text: i18n(
                        "GPU %1",
                        index
                    ),
                    value:
                        "gpu." + index
                }
            )
        }

        var networkNames = []

        for (var name in interfaces)
            networkNames.push(name)

        networkNames.sort()

        var networkModel = [
            {
                text: i18n("Automatic"),
                value: "auto"
            }
        ]

        for (
            var n = 0;
            n < networkNames.length;
            ++n
        ) {
            var interfaceName =
                networkNames[n]

            networkModel.push(
                {
                    text: interfaceName,
                    value: interfaceName
                }
            )
        }

        var storageKeys = []

        for (var storageId in storageTargets)
            storageKeys.push(storageId)

        storageKeys.sort(
            function(a, b) {
                if (a === "storage.root")
                    return -1

                if (b === "storage.root")
                    return 1

                var aName =
                    storageTargets[a]

                var bName =
                    storageTargets[b]

                return aName.localeCompare(
                    bName
                )
            }
        )

        var storageModel = []

        for (
            var s = 0;
            s < storageKeys.length;
            ++s
        ) {
            var storageId =
                storageKeys[s]

            storageModel.push(
                {
                    text:
                        storageTargets[
                            storageId
                        ],
                    value:
                        storageId
                }
            )
        }

        root.storageTargetModel =
            storageModel

        var driveNames = []

        for (var drive in storageDevices)
            driveNames.push(drive)

        driveNames.sort()

        var driveModel = [
            {
                text: i18n("Automatic"),
                value: "auto"
            }
        ]

        for (
            var d = 0;
            d < driveNames.length;
            ++d
        ) {
            var driveName =
                driveNames[d]

            var modelSensor =
                sensors[
                    "storage."
                    + driveName
                    + ".model"
                ]

            var label =
                driveName

            if (
                modelSensor
                && modelSensor.available !== false
                && modelSensor.value
            ) {
                label +=
                    " — "
                    + String(
                        modelSensor.value
                    )
            }

            driveModel.push(
                {
                    text: label,
                    value: driveName
                }
            )
        }

        root.storageDeviceModel =
            driveModel

        root.gpuDeviceModel =
            gpuModel

        root.networkDeviceModel =
            networkModel
    }

    function modelIndex(model, value) {
        for (
            var i = 0;
            i < model.length;
            ++i
        ) {
            if (
                String(model[i].value)
                === String(value)
            )
                return i
        }

        return 0
    }

    Component.onCompleted:
        root.rebuildDeviceModels()

    Timer {
        interval: 2000
        running: true
        repeat: true

        onTriggered:
            root.rebuildDeviceModels()
    }

    property bool cfg_showCpuTemperature: true
    property bool cfg_showCpuFrequency: false

    property bool cfg_showRamUsedTotal: false
    property bool cfg_showRamAvailable: false
    property bool cfg_showRamFree: false
    property bool cfg_showSwapUsedTotal: false
    property bool cfg_showSwapUsage: false

    property bool cfg_showGpuTemperature: true
    property bool cfg_showGpuFanRpm: false
    property bool cfg_showGpuFanPercent: false
    property bool cfg_showGpuCoreClock: false
    property bool cfg_showGpuMemoryClock: false
    property bool cfg_showGpuPower: false
    property bool cfg_showGpuVoltage: false
    property bool cfg_showGpuVram: false

    property bool cfg_showStorageUsedAvailable: false
    property bool cfg_showStorageFilesystem: false
    property bool cfg_showStorageDriveModel: false
    property bool cfg_showStorageDriveHealth: false
    property bool cfg_showStorageDriveTemperature: false
    property bool cfg_showStorageReadRate: false
    property bool cfg_showStorageWriteRate: false
    property bool cfg_showStorageReadIops: false
    property bool cfg_showStorageWriteIops: false
    property bool cfg_showStoragePowerCycles: false
    property bool cfg_showStoragePowerOnHours: false

    property bool cfg_showNetworkRx: false
    property bool cfg_showNetworkTx: false
    property bool cfg_showNetworkLinkSpeed: false

    property bool cfg_showGamingFps: false
    property bool cfg_showGamingFrametime: false
    property bool cfg_showGamingAverageFps: false
    property bool cfg_showGamingOneLow: false
    property bool cfg_showGamingPointOneLow: false

    ColumnLayout {
        width: parent.width
        spacing: Kirigami.Units.largeSpacing

        Label {
            text: i18n("CPU")
            font.bold: true
        }

        CheckBox {
            text: i18n("Temperature")
            checked: root.cfg_showCpuTemperature

            onToggled:
                root.cfg_showCpuTemperature = checked
        }

        CheckBox {
            text: i18n("Frequency")
            checked: root.cfg_showCpuFrequency

            onToggled:
                root.cfg_showCpuFrequency = checked
        }


        Kirigami.Separator {
            Layout.fillWidth: true
        }


        Label {
            text: i18n("Memory")
            font.bold: true
        }

        CheckBox {
            text: i18n("Used / total")
            checked: root.cfg_showRamUsedTotal

            onToggled:
                root.cfg_showRamUsedTotal = checked
        }

        CheckBox {
            text: i18n("Available")
            checked: root.cfg_showRamAvailable

            onToggled:
                root.cfg_showRamAvailable = checked
        }

        CheckBox {
            text: i18n("Free")
            checked: root.cfg_showRamFree

            onToggled:
                root.cfg_showRamFree = checked
        }

        CheckBox {
            text: i18n("Swap used / total")
            checked: root.cfg_showSwapUsedTotal

            onToggled:
                root.cfg_showSwapUsedTotal = checked
        }

        CheckBox {
            text: i18n("Swap usage")
            checked: root.cfg_showSwapUsage

            onToggled:
                root.cfg_showSwapUsage = checked
        }


        Kirigami.Separator {
            Layout.fillWidth: true
        }


        Label {
            text: i18n("GPU")
            font.bold: true
        }

        RowLayout {
            Layout.fillWidth: true

            Label {
                text: i18n("Device")
            }

            ComboBox {
                id: gpuDeviceCombo

                Layout.fillWidth: true

                model:
                    root.gpuDeviceModel

                textRole: "text"
                valueRole: "value"

                currentIndex:
                    root.modelIndex(
                        root.gpuDeviceModel,
                        root.cfg_gpuDevice
                    )

                onActivated: {
                    if (
                        currentIndex >= 0
                        && currentIndex
                            < root.gpuDeviceModel.length
                    ) {
                        root.cfg_gpuDevice =
                            root.gpuDeviceModel[
                                currentIndex
                            ].value
                    }
                }
            }
        }

        CheckBox {
            text: i18n("Temperature")
            checked: root.cfg_showGpuTemperature

            onToggled:
                root.cfg_showGpuTemperature = checked
        }

        CheckBox {
            text: i18n("Fan speed (RPM)")
            checked: root.cfg_showGpuFanRpm

            onToggled:
                root.cfg_showGpuFanRpm = checked
        }

        CheckBox {
            text: i18n("Fan speed (%)")
            checked: root.cfg_showGpuFanPercent

            onToggled:
                root.cfg_showGpuFanPercent = checked
        }

        CheckBox {
            text: i18n("Core clock")
            checked: root.cfg_showGpuCoreClock

            onToggled:
                root.cfg_showGpuCoreClock = checked
        }

        CheckBox {
            text: i18n("Memory clock")
            checked: root.cfg_showGpuMemoryClock

            onToggled:
                root.cfg_showGpuMemoryClock = checked
        }

        CheckBox {
            text: i18n("Power")
            checked: root.cfg_showGpuPower

            onToggled:
                root.cfg_showGpuPower = checked
        }

        CheckBox {
            text: i18n("Voltage")
            checked: root.cfg_showGpuVoltage

            onToggled:
                root.cfg_showGpuVoltage = checked
        }

        CheckBox {
            text: i18n("VRAM used / total")
            checked: root.cfg_showGpuVram

            onToggled:
                root.cfg_showGpuVram = checked
        }
        Kirigami.Separator {
            Layout.fillWidth: true
        }

        Label {
            text: i18n("Storage")
            font.bold: true
        }

        RowLayout {
            Layout.fillWidth: true

            Label {
                text: i18n("Filesystem")
            }

            ComboBox {
                id: storageTargetCombo

                Layout.fillWidth: true

                model:
                    root.storageTargetModel

                textRole: "text"
                valueRole: "value"

                currentIndex:
                    root.modelIndex(
                        root.storageTargetModel,
                        root.cfg_storageTarget
                    )

                onActivated: {
                    if (
                        currentIndex >= 0
                        && currentIndex
                            < root.storageTargetModel.length
                    ) {
                        root.cfg_storageTarget =
                            root.storageTargetModel[
                                currentIndex
                            ].value
                    }
                }
            }
        }

        CheckBox {
            text: i18n("Used / available")
            checked: root.cfg_showStorageUsedAvailable
            onToggled:
                root.cfg_showStorageUsedAvailable = checked
        }

        CheckBox {
            text: i18n("Filesystem")
            checked: root.cfg_showStorageFilesystem
            onToggled:
                root.cfg_showStorageFilesystem = checked
        }


        Label {
            text: i18n("Physical drive")
            font.bold: true
        }

        RowLayout {
            Layout.fillWidth: true

            Label {
                text: i18n("Device")
            }

            ComboBox {
                id: storageDeviceCombo

                Layout.fillWidth: true

                model:
                    root.storageDeviceModel

                textRole: "text"
                valueRole: "value"

                currentIndex:
                    root.modelIndex(
                        root.storageDeviceModel,
                        root.cfg_storageDevice
                    )

                onActivated: {
                    if (
                        currentIndex >= 0
                        && currentIndex
                            < root.storageDeviceModel.length
                    ) {
                        root.cfg_storageDevice =
                            root.storageDeviceModel[
                                currentIndex
                            ].value
                    }
                }
            }
        }

        CheckBox {
            text: i18n("Model")
            checked:
                root.cfg_showStorageDriveModel
            onToggled:
                root.cfg_showStorageDriveModel =
                    checked
        }

        CheckBox {
            text: i18n("SMART health")
            checked:
                root.cfg_showStorageDriveHealth
            onToggled:
                root.cfg_showStorageDriveHealth =
                    checked
        }

        CheckBox {
            text: i18n("Temperature")
            checked:
                root.cfg_showStorageDriveTemperature
            onToggled:
                root.cfg_showStorageDriveTemperature =
                    checked
        }

        CheckBox {
            text: i18n("Read rate")
            checked:
                root.cfg_showStorageReadRate
            onToggled:
                root.cfg_showStorageReadRate =
                    checked
        }

        CheckBox {
            text: i18n("Write rate")
            checked:
                root.cfg_showStorageWriteRate
            onToggled:
                root.cfg_showStorageWriteRate =
                    checked
        }

        CheckBox {
            text: i18n("Read IOPS")
            checked:
                root.cfg_showStorageReadIops
            onToggled:
                root.cfg_showStorageReadIops =
                    checked
        }

        CheckBox {
            text: i18n("Write IOPS")
            checked:
                root.cfg_showStorageWriteIops
            onToggled:
                root.cfg_showStorageWriteIops =
                    checked
        }

        CheckBox {
            text: i18n("Power cycles")
            checked:
                root.cfg_showStoragePowerCycles
            onToggled:
                root.cfg_showStoragePowerCycles =
                    checked
        }

        CheckBox {
            text: i18n("Power-on hours")
            checked:
                root.cfg_showStoragePowerOnHours
            onToggled:
                root.cfg_showStoragePowerOnHours =
                    checked
        }


        Kirigami.Separator {
            Layout.fillWidth: true
        }

        Label {
            text: i18n("Network")
            font.bold: true
        }

        RowLayout {
            Layout.fillWidth: true

            Label {
                text: i18n("Device")
            }

            ComboBox {
                id: networkDeviceCombo

                Layout.fillWidth: true

                model:
                    root.networkDeviceModel

                textRole: "text"
                valueRole: "value"

                currentIndex:
                    root.modelIndex(
                        root.networkDeviceModel,
                        root.cfg_networkDevice
                    )

                onActivated: {
                    if (
                        currentIndex >= 0
                        && currentIndex
                            < root.networkDeviceModel.length
                    ) {
                        root.cfg_networkDevice =
                            root.networkDeviceModel[
                                currentIndex
                            ].value
                    }
                }
            }
        }

        CheckBox {
            text: i18n("Download rate")
            checked: root.cfg_showNetworkRx
            onToggled:
                root.cfg_showNetworkRx = checked
        }

        CheckBox {
            text: i18n("Upload rate")
            checked: root.cfg_showNetworkTx
            onToggled:
                root.cfg_showNetworkTx = checked
        }

        CheckBox {
            text: i18n("Link speed")
            checked: root.cfg_showNetworkLinkSpeed
            onToggled:
                root.cfg_showNetworkLinkSpeed = checked
        }


        Kirigami.Separator {
            Layout.fillWidth: true
        }

        Label {
            text: i18n("Gaming")
            font.bold: true
        }

        CheckBox {
            text: i18n("FPS")
            checked: root.cfg_showGamingFps
            onToggled:
                root.cfg_showGamingFps = checked
        }

        CheckBox {
            text: i18n("Frametime")
            checked: root.cfg_showGamingFrametime
            onToggled:
                root.cfg_showGamingFrametime = checked
        }

        CheckBox {
            text: i18n("Average FPS")
            checked: root.cfg_showGamingAverageFps
            onToggled:
                root.cfg_showGamingAverageFps = checked
        }

        CheckBox {
            text: i18n("1% low")
            checked: root.cfg_showGamingOneLow
            onToggled:
                root.cfg_showGamingOneLow = checked
        }

        CheckBox {
            text: i18n("0.1% low")
            checked: root.cfg_showGamingPointOneLow
            onToggled:
                root.cfg_showGamingPointOneLow = checked
        }

    }
}
