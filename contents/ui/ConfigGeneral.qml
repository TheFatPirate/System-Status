import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property int cfg_refreshMs: 500
    property bool cfg_showCpuTemperature: true
    property bool cfg_showGpuTemperature: true
    property string cfg_temperatureUnit: "C"

    implicitWidth: form.implicitWidth
    implicitHeight: form.implicitHeight

    ColumnLayout {
        id: form

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 12

        Label {
            text: "Telemetry"
            font.bold: true
        }

        CheckBox {
            text: "Show CPU temperature"
            checked: root.cfg_showCpuTemperature

            onToggled:
                root.cfg_showCpuTemperature = checked
        }

        CheckBox {
            text: "Show GPU temperature"
            checked: root.cfg_showGpuTemperature

            onToggled:
                root.cfg_showGpuTemperature = checked
        }

        RowLayout {
            Label {
                text: "Temperature unit:"
            }

            ComboBox {
                model: [
                    "Celsius (°C)",
                    "Fahrenheit (°F)"
                ]

                currentIndex:
                    root.cfg_temperatureUnit === "F"
                    ? 1
                    : 0

                onActivated:
                    root.cfg_temperatureUnit =
                        currentIndex === 1
                        ? "F"
                        : "C"
            }
        }

        Label {
            text: "Refresh"
            font.bold: true
        }

        RowLayout {
            Label {
                text: "Update interval:"
            }

            SpinBox {
                from: 250
                to: 30000
                stepSize: 250

                value: root.cfg_refreshMs

                onValueModified:
                    root.cfg_refreshMs = value
            }

            Label {
                text: "ms"
            }
        }
    }
}
