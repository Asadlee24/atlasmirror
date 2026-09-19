import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: aboutView

    ScrollView {
        anchors.fill: parent
        anchors.margins: 24

        ColumnLayout {
            width: parent.width - 48
            spacing: 16

            Text {
                text: "About AtlasMirror"
                font.pixelSize: 22
                font.bold: true
                color: "#FFFFFF"
            }

            Text {
                text: "Verified OpenStreetMap snapshots distributed through Logos."
                font.pixelSize: 14
                color: "#AAAAAA"
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#222222" }

            // Metadata Grid
            GridLayout {
                columns: 2
                rowSpacing: 10
                columnSpacing: 20

                Text { text: "Version:"; color: "#888888" }
                Text { text: "v0.1.0-alpha"; color: "#FFFFFF"; font.family: "monospace" }

                Text { text: "Logos Core SDK:"; color: "#888888" }
                Text { text: "atlasmirror-sdk v0.1.0"; color: "#FFFFFF"; font.family: "monospace" }

                Text { text: "LEZ Program ID:"; color: "#888888" }
                Text { text: "0xosm_registry_testnet03"; color: "#FFFFFF"; font.family: "monospace" }

                Text { text: "Target Network:"; color: "#888888" }
                Text { text: "Logos Testnet 0.3"; color: "#FFFFFF" }

                Text { text: "Prize Target:"; color: "#888888" }
                Text { text: "Logos λPrize LP-0018"; color: "#FFFFFF" }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#222222" }

            // Attribution & Licensing
            Text {
                text: "Attribution & Legal"
                font.pixelSize: 16
                font.bold: true
                color: "#FFFFFF"
            }

            Text {
                text: "Map data © OpenStreetMap contributors.\nOpenStreetMap data is licensed under the Open Data Commons Open Database License (ODbL)."
                color: "#CCCCCC"
                font.pixelSize: 12
                lineHeight: 1.4
            }

            Text {
                text: "Snapshot extracts, indices, and checksums are provided by Geofabrik GmbH."
                color: "#AAAAAA"
                font.pixelSize: 12
            }

            Text {
                text: "AtlasMirror source code is dual-licensed under the MIT License and Apache License 2.0."
                color: "#AAAAAA"
                font.pixelSize: 12
            }

            Item { Layout.fillHeight: true }

            Text {
                text: "Built on Logos. Content over decoration. Utility over aesthetics."
                color: "#666666"
                font.pixelSize: 11
            }
        }
    }
}
