import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: registryView

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        Text {
            text: "On-Chain LEZ Registry Inspector"
            font.pixelSize: 18
            font.bold: true
            color: "#FFFFFF"
        }

        // Query Bar
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            ComboBox {
                id: queryType
                model: ["Region Path", "Parent Identifier", "Storage CID"]
                Layout.preferredWidth: 160
            }

            TextField {
                id: queryInput
                Layout.fillWidth: true
                placeholderText: "Enter query parameter (e.g. 'asia/pakistan' or 'bafybeic7vj...')"
                color: "#FFFFFF"
                font.family: "monospace"
                background: Rectangle {
                    color: "#111111"
                    border.color: "#333333"
                    radius: 2
                }
            }

            Button {
                text: "Query On-Chain"
                onClicked: {
                    rawOutput.text = JSON.stringify({
                        "program_id": "0xosm_registry_testnet03",
                        "query_type": queryType.currentText,
                        "query_value": queryInput.text,
                        "result": {
                            "region": "asia/pakistan",
                            "parent": null,
                            "level": "Country",
                            "cid": "bafybeic7vj2k...4q",
                            "source_url": "https://download.geofabrik.de/asia/pakistan-latest.osm.pbf",
                            "checksum": "378df25f824177ebcbe9aa11d88bbd6b",
                            "version": "2026-09-19",
                            "hosted": true,
                            "timestamp": 1726747200
                        }
                    }, null, 2)
                }
            }
        }

        // Raw Output Box
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#0A0A0A"
            border.color: "#222222"

            ScrollView {
                anchors.fill: parent
                anchors.margins: 12

                TextArea {
                    id: rawOutput
                    readOnly: true
                    text: "// Execute a query above to inspect raw on-chain state from the LEZ SPEL program."
                    color: "#00FF66"
                    font.family: "monospace"
                    font.pixelSize: 12
                    background: Rectangle { color: "transparent" }
                }
            }
        }
    }
}
