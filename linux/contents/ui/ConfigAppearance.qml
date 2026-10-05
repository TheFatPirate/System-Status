import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Item {
    id: root

    property bool cfg_compact: false
    property bool cfg_showUnits: true
    property bool cfg_showIcons: true

    property int cfg_usageWarning: 75
    property int cfg_usageCritical: 90

    property int cfg_cpuTempWarning: 80
    property int cfg_cpuTempCritical: 90

    property int cfg_gpuTempWarning: 85
    property int cfg_gpuTempCritical: 95

    property string cfg_warningColor: "#ff9d00"
    property string cfg_criticalColor: "#ff3030"

    implicitWidth: form.implicitWidth
    implicitHeight: form.implicitHeight

    ColumnLayout {
        id: form

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 10

        Label {
            text: "Warnings"
            font.bold: true
        }

        Label {
            text: "Usage"
            font.bold: true
        }

        RowLayout {
            Label {
                text: "Warning:"
                Layout.preferredWidth: 100
            }

            SpinBox {
                from: 1
                to: 99

                value: root.cfg_usageWarning

                onValueModified:
                    root.cfg_usageWarning = value
            }

            Label {
                text: "%"
            }
        }

        RowLayout {
            Label {
                text: "Critical:"
                Layout.preferredWidth: 100
            }

            SpinBox {
                from: 1
                to: 100

                value: root.cfg_usageCritical

                onValueModified:
                    root.cfg_usageCritical = value
            }

            Label {
                text: "%"
            }
        }

        Label {
            text: "CPU Temperature"
            font.bold: true
        }

        RowLayout {
            Label {
                text: "Warning:"
                Layout.preferredWidth: 100
            }

            SpinBox {
                from: 30
                to: 120
                value: root.cfg_cpuTempWarning

                onValueModified:
                    root.cfg_cpuTempWarning = value
            }

            Label {
                text: "°C"
            }
        }

        RowLayout {
            Label {
                text: "Critical:"
                Layout.preferredWidth: 100
            }

            SpinBox {
                from: 30
                to: 120
                value: root.cfg_cpuTempCritical

                onValueModified:
                    root.cfg_cpuTempCritical = value
            }

            Label {
                text: "°C"
            }
        }

        Label {
            text: "GPU Temperature"
            font.bold: true
        }

        RowLayout {
            Label {
                text: "Warning:"
                Layout.preferredWidth: 100
            }

            SpinBox {
                from: 30
                to: 120
                value: root.cfg_gpuTempWarning

                onValueModified:
                    root.cfg_gpuTempWarning = value
            }

            Label {
                text: "°C"
            }
        }

        RowLayout {
            Label {
                text: "Critical:"
                Layout.preferredWidth: 100
            }

            SpinBox {
                from: 30
                to: 120
                value: root.cfg_gpuTempCritical

                onValueModified:
                    root.cfg_gpuTempCritical = value
            }

            Label {
                text: "°C"
            }
        }

        Label {
            text: "Pulse Colors"
            font.bold: true
        }

        RowLayout {
            Label {
                text: "Warning:"
                Layout.preferredWidth: 100
            }

            Button {
                text: root.cfg_warningColor

                onClicked:
                    warningDialog.open()
            }
        }

        RowLayout {
            Label {
                text: "Critical:"
                Layout.preferredWidth: 100
            }

            Button {
                text: root.cfg_criticalColor

                onClicked:
                    criticalDialog.open()
            }
        }
    }

    ColorDialog {
        id: warningDialog

        title: "Warning pulse color"
        selectedColor: root.cfg_warningColor

        onAccepted:
            root.cfg_warningColor =
                selectedColor.toString()
    }

    ColorDialog {
        id: criticalDialog

        title: "Critical pulse color"
        selectedColor: root.cfg_criticalColor

        onAccepted:
            root.cfg_criticalColor =
                selectedColor.toString()
    }
}
