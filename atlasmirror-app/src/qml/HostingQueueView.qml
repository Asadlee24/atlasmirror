import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: queueView

    ListModel {
        id: queueModel
        ListElement { region: "us/texas"; state: "DOWNLOADING"; progress: 0.45; error: "" }
        ListElement { region: "china/guangdong"; state: "VERIFYING"; progress: 0.80; error: "" }
        ListElement { region: "europe/poland"; state: "UPLOADING_STORAGE"; progress: 0.60; error: "" }
        ListElement { region: "africa/egypt"; state: "REGISTERING"; progress: 0.95; error: "" }
        ListElement { region: "asia/iran"; state: "FAILED"; progress: 0.20; error: "CHECKSUM_MISMATCH: corrupt download" }
        ListElement { region: "south-america/brazil"; state: "COMPLETE"; progress: 1.0; error: "" }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Text {
                text: "Hosting Pipeline Queue"
                font.pixelSize: 18
                font.bold: true
                color: "#FFFFFF"
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "Clear Completed"
                onClicked: console.log("Cleared finished jobs")
            }

            Button {
                text: "Retry All Failed"
                onClicked: console.log("Retrying failed jobs")
            }
        }

        // State Machine Legend
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            color: "#111111"
            border.color: "#222222"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 16

                Text { text: "Pipeline States:"; color: "#888888"; font.bold: true }
                Text { text: "QUEUED → FETCHING_METADATA → DOWNLOADING → VERIFYING → UPLOADING_STORAGE → REGISTERING → CONFIRMING → COMPLETE"; color: "#AAAAAA"; font.family: "monospace"; font.pixelSize: 11 }
            }
        }

        // Queue ListView
        ListView {
            id: queueList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: queueModel
            spacing: 8

            delegate: Rectangle {
                width: queueList.width
                height: 64
                color: "#111111"
                border.color: model.state === "FAILED" ? "#990000" : (model.state === "COMPLETE" ? "#2E7D32" : "#333333")

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 16

                    ColumnLayout {
                        Layout.preferredWidth: 200
                        spacing: 4

                        Text {
                            text: model.region
                            color: "#FFFFFF"
                            font.bold: true
                            font.family: "monospace"
                        }
                        Text {
                            text: model.error !== "" ? model.error : "Phase: " + model.state
                            color: model.state === "FAILED" ? "#FF5555" : "#888888"
                            font.pixelSize: 11
                            elide: Text.ElideRight
                        }
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
                        Layout.preferredWidth: 140
                        Layout.preferredHeight: 28
                        color: model.state === "COMPLETE" ? "#1B5E20" : (model.state === "FAILED" ? "#B71C1C" : "#0D47A1")
                        radius: 2

                        Text {
                            anchors.centerIn: parent
                            text: model.state
                            color: "#FFFFFF"
                            font.bold: true
                            font.pixelSize: 11
                        }
                    }

                    Button {
                        text: model.state === "FAILED" ? "Retry" : "Cancel"
                        enabled: model.state !== "COMPLETE"
                        onClicked: console.log("Action on job:", model.region)
                    }
                }
            }
        }
    }
}
