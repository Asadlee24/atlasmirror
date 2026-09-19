import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: regionsView

    // Predefined non-overlapping regions catalog
    ListModel {
        id: regionsModel
        ListElement { region: "asia/pakistan"; name: "Pakistan"; level: "country"; version: "—"; hosted: false; cid: "—"; updateStatus: "NOT_HOSTED"; checksum: "—" }
        ListElement { region: "europe/germany"; name: "Germany"; level: "country"; version: "—"; hosted: false; cid: "—"; updateStatus: "NOT_HOSTED"; checksum: "—" }
        ListElement { region: "europe/france"; name: "France"; level: "country"; version: "—"; hosted: false; cid: "—"; updateStatus: "NOT_HOSTED"; checksum: "—" }
        ListElement { region: "us/california"; name: "California"; level: "subregion"; version: "—"; hosted: false; cid: "—"; updateStatus: "NOT_HOSTED"; checksum: "—" }
        ListElement { region: "us/texas"; name: "Texas"; level: "subregion"; version: "—"; hosted: false; cid: "—"; updateStatus: "NOT_HOSTED"; checksum: "—" }
        ListElement { region: "india/northern-zone"; name: "Northern Zone"; level: "subregion"; version: "—"; hosted: false; cid: "—"; updateStatus: "NOT_HOSTED"; checksum: "—" }
        ListElement { region: "china/guangdong"; name: "Guangdong"; level: "subregion"; version: "—"; hosted: false; cid: "—"; updateStatus: "NOT_HOSTED"; checksum: "—" }
        ListElement { region: "russia/central-fed-district"; name: "Central Federal District"; level: "subregion"; version: "—"; hosted: false; cid: "—"; updateStatus: "NOT_HOSTED"; checksum: "—" }
    }

    property var selectedItem: null

    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        // Left: Table & Controls
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12

            // Filter Bar
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                TextField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholderText: "Search region by path or name..."
                    color: "#FFFFFF"
                    background: Rectangle {
                        color: "#111111"
                        border.color: "#333333"
                        radius: 2
                    }
                }

                ComboBox {
                    id: filterCombo
                    model: ["All", "Hosted", "Not hosted", "Update available"]
                    background: Rectangle {
                        color: "#111111"
                        border.color: "#333333"
                        radius: 2
                    }
                }

                Button {
                    text: "Refresh Index"
                    onClicked: console.log("Fetching live Geofabrik index...")
                }
            }

            // Regions Table Header
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 32
                color: "#1A1A1A"
                border.color: "#333333"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12

                    Text { text: "Region"; color: "#AAAAAA"; font.bold: true; Layout.preferredWidth: 200 }
                    Text { text: "Level"; color: "#AAAAAA"; font.bold: true; Layout.preferredWidth: 100 }
                    Text { text: "Version"; color: "#AAAAAA"; font.bold: true; Layout.preferredWidth: 100 }
                    Text { text: "Storage Status"; color: "#AAAAAA"; font.bold: true; Layout.preferredWidth: 120 }
                    Text { text: "CID"; color: "#AAAAAA"; font.bold: true; Layout.fillWidth: true }
                    Text { text: "Action"; color: "#AAAAAA"; font.bold: true; Layout.preferredWidth: 100 }
                }
            }

            // Table ListView
            ListView {
                id: regionsList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: regionsModel

                delegate: Rectangle {
                    width: regionsList.width
                    height: 40
                    color: mouseArea.containsMouse ? "#1A1A1A" : (index % 2 === 0 ? "#0A0A0A" : "#000000")
                    border.color: selectedItem === model ? "#0066CC" : "transparent"

                    MouseArea {
                        id: mouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: selectedItem = model
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12

                        Text { text: model.region; color: "#FFFFFF"; font.family: "monospace"; Layout.preferredWidth: 200 }
                        Text { text: model.level; color: "#888888"; Layout.preferredWidth: 100 }
                        Text { text: model.version; color: "#888888"; Layout.preferredWidth: 100 }
                        Text {
                            text: model.hosted ? "Hosted" : "Not hosted"
                            color: model.hosted ? "#4CAF50" : "#888888"
                            font.bold: true
                            Layout.preferredWidth: 120
                        }
                        Text { text: model.cid; color: "#AAAAAA"; font.family: "monospace"; elide: Text.ElideRight; Layout.fillWidth: true }
                        Button {
                            text: model.hosted ? "Download" : "Host"
                            Layout.preferredWidth: 90
                            onClicked: console.log("Action triggered for:", model.region)
                        }
                    }
                }
            }
        }

        // Right: Inspector Panel
        Rectangle {
            Layout.preferredWidth: 320
            Layout.fillHeight: true
            color: "#111111"
            border.color: "#222222"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                Text {
                    text: "Region Details"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#FFFFFF"
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: "#222222" }

                Text { text: "Canonical Path:"; color: "#888888"; font.pixelSize: 12 }
                Text { text: selectedItem ? selectedItem.region : "Select a region"; color: "#FFFFFF"; font.family: "monospace" }

                Text { text: "Hierarchy Level:"; color: "#888888"; font.pixelSize: 12 }
                Text { text: selectedItem ? selectedItem.level : "—"; color: "#FFFFFF" }

                Text { text: "Storage CID:"; color: "#888888"; font.pixelSize: 12 }
                Text { text: selectedItem ? selectedItem.cid : "—"; color: "#FFFFFF"; font.family: "monospace"; elide: Text.ElideRight; Layout.fillWidth: true }

                Text { text: "MD5 Checksum:"; color: "#888888"; font.pixelSize: 12 }
                Text { text: selectedItem ? selectedItem.checksum : "—"; color: "#FFFFFF"; font.family: "monospace"; elide: Text.ElideRight; Layout.fillWidth: true }

                Text { text: "Upstream Version:"; color: "#888888"; font.pixelSize: 12 }
                Text { text: selectedItem ? selectedItem.version : "—"; color: "#FFFFFF" }

                Item { Layout.fillHeight: true }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Button {
                        text: "Copy CID"
                        Layout.fillWidth: true
                        enabled: selectedItem && selectedItem.hosted
                        onClicked: console.log("Copied CID:", selectedItem.cid)
                    }

                    Button {
                        text: "Host Region"
                        Layout.fillWidth: true
                        enabled: selectedItem && !selectedItem.hosted
                        onClicked: console.log("Hosting region:", selectedItem.region)
                    }
                }
            }
        }
    }
}
