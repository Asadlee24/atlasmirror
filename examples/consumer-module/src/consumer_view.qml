import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: consumerRoot
    width: 640
    height: 520
    color: "#0D1117"

    // Resolves genuine AtlasMirror SDK module without depending on AtlasMirror UI
    property var osmSdk: (typeof logos !== "undefined" && logos.module) ? logos.module("atlasmirror_sdk") : (typeof atlasmirrorSdk !== "undefined" ? atlasmirrorSdk : null)

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 16
        width: 520

        Text {
            text: "Third-Party Basecamp Consumer Example"
            color: "#FFFFFF"
            font.pixelSize: 18
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        Text {
            text: "Demonstrates consuming 'atlasmirror_sdk' in an independent Basecamp application to query on-chain records and retrieve verified OSM snapshots."
            color: "#8B949E"
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        // Region Selection & Query Panel
        Rectangle {
            Layout.fillWidth: true
            height: 180
            color: "#161B22"
            border.color: "#30363D"
            radius: 6

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Target Region:"; color: "#8B949E"; font.bold: true; Layout.preferredWidth: 100 }
                    ComboBox {
                        id: regionSelector
                        Layout.fillWidth: true
                        model: ["asia/pakistan", "europe/germany", "europe/france", "us/california", "india/northern-zone"]
                        background: Rectangle {
                            color: "#0D1117"
                            border.color: "#30363D"
                            radius: 4
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Resolved CID:"; color: "#8B949E"; font.bold: true; Layout.preferredWidth: 100 }
                    Text {
                        id: cidLabel
                        text: "—"
                        color: "#58A6FF"
                        font.family: "monospace"
                        font.pixelSize: 12
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Published MD5:"; color: "#8B949E"; font.bold: true; Layout.preferredWidth: 100 }
                    Text {
                        id: md5Label
                        text: "—"
                        color: "#7EE787"
                        font.family: "monospace"
                        font.pixelSize: 12
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Pipeline State:"; color: "#8B949E"; font.bold: true; Layout.preferredWidth: 100 }
                    Text {
                        id: statusLabel
                        text: osmSdk ? "SDK Initialized. Ready to query." : "Awaiting Basecamp SDK context..."
                        color: osmSdk ? "#3FB950" : "#D29922"
                        font.pixelSize: 12
                        Layout.fillWidth: true
                    }
                }
            }
        }

        // Action Buttons
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Button {
                text: "1. Resolve Region On-Chain"
                Layout.fillWidth: true
                onClicked: {
                    var target = regionSelector.currentText
                    if (!osmSdk) {
                        statusLabel.text = "Error: 'atlasmirror_sdk' service is not available in current runtime."
                        statusLabel.color = "#F85149"
                        return
                    }
                    try {
                        var resStr = osmSdk.resolveRegion(target)
                        var obj = JSON.parse(resStr)
                        if (obj.hosted && obj.cid) {
                            cidLabel.text = obj.cid
                            md5Label.text = obj.checksum || "Verified"
                            statusLabel.text = "Resolved on-chain via Testnet 0.3 (Version: " + (obj.version || "latest") + ")"
                            statusLabel.color = "#3FB950"
                        } else if (obj.hosted === false) {
                            cidLabel.text = "Not hosted on Logos Storage yet"
                            md5Label.text = "—"
                            statusLabel.text = "Region is registered in catalog but unhosted. Fallback: " + (obj.fallback_url || "Geofabrik")
                            statusLabel.color = "#D29922"
                        } else {
                            statusLabel.text = "Response: " + resStr
                            statusLabel.color = "#F85149"
                        }
                    } catch(e) {
                        statusLabel.text = "JSON parsing error: " + e
                        statusLabel.color = "#F85149"
                    }
                }
            }

            Button {
                text: "2. Download Verified PBF"
                Layout.fillWidth: true
                highlighted: true
                onClicked: {
                    var target = regionSelector.currentText
                    if (!osmSdk) {
                        statusLabel.text = "Error: 'atlasmirror_sdk' service is not available in current runtime."
                        statusLabel.color = "#F85149"
                        return
                    }
                    var cleanName = target.replace('/', '_')
                    var dest = "/tmp/" + cleanName + "-latest.osm.pbf"
                    statusLabel.text = "Initiating streaming download & MD5 verification..."
                    statusLabel.color = "#58A6FF"

                    var ok = false
                    try {
                        ok = osmSdk.downloadRegion(target, dest)
                        if (ok) {
                            statusLabel.text = "Download verified & saved to " + dest
                            statusLabel.color = "#3FB950"
                        } else {
                            statusLabel.text = "Download failed: checksum mismatch or storage unreachable."
                            statusLabel.color = "#F85149"
                        }
                    } catch(e) {
                        statusLabel.text = "SDK call failed: " + e
                        statusLabel.color = "#F85149"
                    }
                }
            }
        }
    }
}
