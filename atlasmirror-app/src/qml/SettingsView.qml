import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: settingsView

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 20

        Text {
            text: "System & Network Settings"
            font.pixelSize: 18
            font.bold: true
            color: "#FFFFFF"
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#222222" }

        // Settings Form
        GridLayout {
            columns: 2
            rowSpacing: 16
            columnSpacing: 24
            Layout.fillWidth: true

            Text { text: "Logos LEZ Sequencer RPC:"; color: "#AAAAAA" }
            TextField {
                text: "http://127.0.0.1:8545"
                color: "#FFFFFF"
                font.family: "monospace"
                Layout.fillWidth: true
                background: Rectangle { color: "#111111"; border.color: "#333333"; radius: 2 }
            }

            Text { text: "Logos Storage Endpoint:"; color: "#AAAAAA" }
            TextField {
                text: "http://127.0.0.1:5001"
                color: "#FFFFFF"
                font.family: "monospace"
                Layout.fillWidth: true
                background: Rectangle { color: "#111111"; border.color: "#333333"; radius: 2 }
            }

            Text { text: "Download Directory:"; color: "#AAAAAA" }
            TextField {
                text: "/var/lib/atlasmirror/downloads"
                color: "#FFFFFF"
                font.family: "monospace"
                Layout.fillWidth: true
                background: Rectangle { color: "#111111"; border.color: "#333333"; radius: 2 }
            }

            Text { text: "Max Concurrent Hosts:"; color: "#AAAAAA" }
            SpinBox {
                from: 1
                to: 5
                value: 2
            }

            Text { text: "Max Storage Retries:"; color: "#AAAAAA" }
            SpinBox {
                from: 1
                to: 10
                value: 5
            }

            Text { text: "Anonymous Analytics (Opt-In):"; color: "#AAAAAA" }
            CheckBox {
                checked: false
                text: "Disabled (Strictly Zero Telemetry by Default)"
            }
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Button {
                text: "Reset Defaults"
            }
            Button {
                text: "Save Settings"
                highlighted: true
            }
        }
    }
}
