import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: queueView

    ListModel {
        id: queueModel
        ListElement { region: "africa/ethiopia"; state: "COMPLETE"; progress: 1.0; error: "" }
        ListElement { region: "asia/pakistan"; state: "COMPLETE"; progress: 1.0; error: "" }
        ListElement { region: "china/henan"; state: "COMPLETE"; progress: 1.0; error: "" }
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
                onClicked: {
                    if (typeof backend !== "undefined" && backend.clearCompletedQueue) {
                        backend.clearCompletedQueue()
                    }
                    for (var i = queueModel.count - 1; i >= 0; --i) {
                        if (queueModel.get(i).state === "COMPLETE") {
                            queueModel.remove(i)
                        }
                    }
                }
            }

            Button {
                text: "Retry Failed"
                onClicked: {
                    if (typeof backend !== "undefined" && backend.retryAllFailed) {
                        backend.retryAllFailed()
                    }
                }
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
                Text { text: "QUEUED → DOWNLOADING → VERIFYING MD5 → UPLOADING STORAGE → ON-CHAIN REGISTER → COMPLETE"; color: "#AAAAAA"; font.family: "monospace"; font.pixelSize: 11 }
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
                        Layout.preferredWidth: 220
                        spacing: 4

                        Text {
                            text: model.region
                            color: "#FFFFFF"
                            font.bold: true
                            font.family: "monospace"
                        }
                        Text {
                            text: model.error !== "" ? model.error : "Phase: " + model.state
                            color: model.state === "FAILED" ? "#FF5555" : (model.state === "COMPLETE" ? "#4CAF50" : "#888888")
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

                    Button {
                        text: model.state === "FAILED" ? "Retry" : "Cancel"
                        enabled: model.state !== "COMPLETE"
                        Layout.preferredWidth: 80
                        onClicked: {
                            if (model.state === "FAILED") {
                                if (typeof backend !== "undefined" && backend.retryHost) {
                                    backend.retryHost(model.region)
                                }
                            } else {
                                if (typeof backend !== "undefined" && backend.cancelHost) {
                                    backend.cancelHost(model.region)
                                }
                                model.state = "CANCELLED"
                            }
                        }
                    }
                }
            }
        }
    }
}
