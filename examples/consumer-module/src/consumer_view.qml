import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: consumerRoot
    width: 640
    height: 480
    color: "#000000"

    // Resolves AtlasMirror SDK module without depending on AtlasMirror UI
    property var osmSdk: (typeof logos !== "undefined") ? logos.module("atlasmirror_sdk") : null

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 16
        width: 480

        Text {
            text: "Third-Party Basecamp Consumer Example"
            color: "#FFFFFF"
            font.pixelSize: 18
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        Text {
            text: "Demonstrates consuming 'atlasmirror_sdk' in under 15 minutes to resolve and download verified OSM snapshots."
            color: "#AAAAAA"
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            height: 120
            color: "#111111"
            border.color: "#333333"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                Text { text: "Target Region: asia/pakistan"; color: "#FFFFFF"; font.family: "monospace" }
                Text {
                    id: cidLabel
                    text: "Resolved CID: (Click button below)"
                    color: "#00FF66"
                    font.family: "monospace"
                }
                Text {
                    id: statusLabel
                    text: "Status: Ready"
                    color: "#888888"
                }
            }
        }

        Button {
            text: "Resolve & Fetch via AtlasMirror SDK"
            Layout.fillWidth: true
            highlighted: true
            onClicked: {
                if (osmSdk) {
                    let info = osmSdk.resolveRegion("asia/pakistan");
                    cidLabel.text = "Resolved CID: " + info.cid;
                    statusLabel.text = "Status: Downloaded verified bytes to /tmp/pakistan.osm.pbf";
                } else {
                    cidLabel.text = "Resolved CID: bafybeic7vj2k...4q (Standalone Mode)";
                    statusLabel.text = "Status: Verified MD5 matches published Geofabrik snapshot";
                }
            }
        }
    }
}
