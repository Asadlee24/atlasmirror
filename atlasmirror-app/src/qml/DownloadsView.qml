import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: downloadsView

    ListModel {
        id: downloadsModel
        ListElement { region: "asia/pakistan"; source: "Logos Storage (CID: bafybeic7vj...)"; size: "118 MB"; progress: 1.0; status: "VERIFIED" }
        ListElement { region: "europe/germany"; source: "Logos Storage (CID: bafybeih4nm...)"; size: "3.8 GB"; progress: 0.65; status: "DOWNLOADING" }
        ListElement { region: "us/texas"; source: "Geofabrik (Central Fallback)"; size: "1.4 GB"; progress: 0.30; status: "DOWNLOADING" }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Text {
                text: "Local Snapshot Downloads"
                font.pixelSize: 18
                font.bold: true
                color: "#FFFFFF"
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "Open Download Directory"
                onClicked: console.log("Opening downloads directory...")
            }
        }

        ListView {
            id: downloadsList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: downloadsModel
            spacing: 8

            delegate: Rectangle {
                width: downloadsList.width
                height: 56
                color: "#111111"
                border.color: "#222222"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 16

                    ColumnLayout {
                        Layout.preferredWidth: 220
                        spacing: 2

                        Text {
                            text: model.region
                            color: "#FFFFFF"
                            font.bold: true
                            font.family: "monospace"
                        }
                        Text {
                            text: model.source
                            color: model.source.indexOf("Central Fallback") !== -1 ? "#FF9800" : "#888888"
                            font.pixelSize: 11
                            elide: Text.ElideRight
                        }
                    }

                    Text {
                        text: model.size
                        color: "#AAAAAA"
                        font.family: "monospace"
                        Layout.preferredWidth: 80
                    }

                    ProgressBar {
                        Layout.fillWidth: true
                        value: model.progress
                    }

                    Text {
                        text: Math.round(model.progress * 100) + "%"
                        color: "#FFFFFF"
                        font.family: "monospace"
                        Layout.preferredWidth: 48
                    }

                    Rectangle {
                        Layout.preferredWidth: 100
                        Layout.preferredHeight: 24
                        color: model.status === "VERIFIED" ? "#1B5E20" : "#333333"
                        radius: 2

                        Text {
                            anchors.centerIn: parent
                            text: model.status
                            color: "#FFFFFF"
                            font.bold: true
                            font.pixelSize: 10
                        }
                    }
                }
            }
        }
    }
}
