import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: registryView

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "On-Chain LEZ Registry Inspector"
                font.pixelSize: 18
                font.bold: true
                color: "#FFFFFF"
            }
            Item { Layout.fillWidth: true }
            Text {
                text: "Program: bcdc1042...8b4f • Account: T8T4nf...vci"
                color: "#888888"
                font.family: "monospace"
                font.pixelSize: 11
            }
        }

        // Query Bar
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            ComboBox {
                id: queryType
                model: ["Region Path", "Storage CID", "Parent Subregions"]
                Layout.preferredWidth: 180
                background: Rectangle {
                    color: "#111111"
                    border.color: "#333333"
                    radius: 2
                }
            }

            TextField {
                id: queryInput
                Layout.fillWidth: true
                placeholderText: "Enter canonical path (e.g. 'asia/pakistan') or CID (e.g. 'zDvZRwzm9WQQ...')"
                color: "#FFFFFF"
                font.family: "monospace"
                background: Rectangle {
                    color: "#111111"
                    border.color: "#333333"
                    radius: 2
                }
                onAccepted: executeQuery()
            }

            Button {
                text: "Query On-Chain"
                onClicked: executeQuery()
            }
        }

        function executeQuery() {
            var val = queryInput.text.trim()
            if (val === "") {
                rawOutput.text = "// Please enter a region path or CID above."
                return
            }

            if (typeof backend !== "undefined" && backend.queryRegistry) {
                var res = backend.queryRegistry(queryType.currentText, val)
                rawOutput.text = res
            } else {
                rawOutput.text = JSON.stringify({
                    "error": "BACKEND_UNAVAILABLE",
                    "message": "Cannot reach backend / on-chain registry SDK."
                }, null, 2)
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
                    text: "// Enter a canonical region path (e.g. 'asia/pakistan') and click 'Query On-Chain' to inspect live state."
                    color: "#00FF66"
                    font.family: "monospace"
                    font.pixelSize: 12
                    background: Rectangle { color: "transparent" }
                }
            }
        }
    }
}
