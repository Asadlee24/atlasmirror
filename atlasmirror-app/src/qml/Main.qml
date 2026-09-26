import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    width: 1024
    height: 720
    title: "AtlasMirror — Verified OpenStreetMap snapshots on Logos"
    color: "#000000"

    // Theme Palette
    readonly property color bgDark: "#000000"
    readonly property color bgSurface: "#111111"
    readonly property color borderDark: "#222222"
    readonly property color textPrimary: "#FFFFFF"
    readonly property color textSecondary: "#888888"
    readonly property color accentBlue: "#0066CC"

    // Backend controller interface for all child QML views
    QtObject {
        id: backend

        property var regions: (typeof cBackend !== "undefined" && cBackend.regions) ? cBackend.regions : []
        property var queue: (typeof cBackend !== "undefined" && cBackend.queue) ? cBackend.queue : []
        property var downloads: (typeof cBackend !== "undefined" && cBackend.downloads) ? cBackend.downloads : []

        signal regionsUpdated()
        signal queueUpdated()
        signal downloadsUpdated()

        Component.onCompleted: {
            if (typeof cBackend !== "undefined") {
                try {
                    cBackend.regionsUpdated.connect(function() {
                        backend.regions = cBackend.regions;
                        backend.regionsUpdated();
                    });
                    cBackend.queueUpdated.connect(function() {
                        backend.queue = cBackend.queue;
                        backend.queueUpdated();
                    });
                    cBackend.downloadsUpdated.connect(function() {
                        backend.downloads = cBackend.downloads;
                        backend.downloadsUpdated();
                    });
                } catch(e) {
                    console.log("Signal connection note:", e);
                }
            }
        }

        function refreshIndex() {
            if (typeof cBackend !== "undefined") cBackend.refreshIndex();
        }

        function hostRegion(path) {
            if (typeof cBackend !== "undefined") cBackend.hostRegion(path);
        }

        function startBulkHost(paths) {
            if (typeof cBackend !== "undefined") cBackend.startBulkHost(paths);
        }

        function cancelHost(path) {
            if (typeof cBackend !== "undefined") cBackend.cancelHost(path);
        }

        function retryHost(path) {
            if (typeof cBackend !== "undefined") cBackend.retryHost(path);
        }

        function clearCompletedQueue() {
            if (typeof cBackend !== "undefined") cBackend.clearCompletedQueue();
        }

        function retryAllFailed() {
            if (typeof cBackend !== "undefined") cBackend.retryAllFailed();
        }

        function startDownload(path) {
            if (typeof cBackend !== "undefined") cBackend.startDownload(path);
        }

        function copyToClipboard(text) {
            if (typeof cBackend !== "undefined") cBackend.copyToClipboard(text);
        }

        function queryRegistry(type, val) {
            return (typeof cBackend !== "undefined") ? cBackend.queryRegistry(type, val) : "";
        }

        function importLocal(path, file) {
            return (typeof cBackend !== "undefined") ? cBackend.importLocal(path, file) : "";
        }

        function updateCheck(path) {
            return (typeof cBackend !== "undefined") ? cBackend.updateCheck(path) : "";
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            color: root.bgSurface
            border.color: root.borderDark
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 16

                Text {
                    text: "AtlasMirror"
                    font.pixelSize: 18
                    font.bold: true
                    color: root.textPrimary
                }

                Rectangle {
                    width: 1
                    height: 20
                    color: root.borderDark
                }

                Text {
                    text: "Verified OpenStreetMap snapshots on Logos"
                    font.pixelSize: 13
                    color: root.textSecondary
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: "Built on Logos • LP-0018"
                    font.pixelSize: 12
                    color: root.textSecondary
                }
            }
        }

        // Tab Navigation
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            color: root.bgDark
            border.color: root.borderDark
            border.width: 1

            TabBar {
                id: navTabBar
                anchors.fill: parent
                background: Rectangle { color: "transparent" }

                TabButton {
                    text: "Regions"
                    contentItem: Text {
                        text: parent.text
                        color: parent.checked ? root.textPrimary : root.textSecondary
                        font.bold: parent.checked
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: parent.checked ? root.bgSurface : "transparent"
                        border.color: parent.checked ? root.borderDark : "transparent"
                    }
                }
                TabButton {
                    text: "Hosting Queue"
                    contentItem: Text {
                        text: parent.text
                        color: parent.checked ? root.textPrimary : root.textSecondary
                        font.bold: parent.checked
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: parent.checked ? root.bgSurface : "transparent"
                        border.color: parent.checked ? root.borderDark : "transparent"
                    }
                }
                TabButton {
                    text: "Downloads"
                    contentItem: Text {
                        text: parent.text
                        color: parent.checked ? root.textPrimary : root.textSecondary
                        font.bold: parent.checked
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: parent.checked ? root.bgSurface : "transparent"
                        border.color: parent.checked ? root.borderDark : "transparent"
                    }
                }
                TabButton {
                    text: "Registry"
                    contentItem: Text {
                        text: parent.text
                        color: parent.checked ? root.textPrimary : root.textSecondary
                        font.bold: parent.checked
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: parent.checked ? root.bgSurface : "transparent"
                        border.color: parent.checked ? root.borderDark : "transparent"
                    }
                }
                TabButton {
                    text: "Settings"
                    contentItem: Text {
                        text: parent.text
                        color: parent.checked ? root.textPrimary : root.textSecondary
                        font.bold: parent.checked
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: parent.checked ? root.bgSurface : "transparent"
                        border.color: parent.checked ? root.borderDark : "transparent"
                    }
                }
                TabButton {
                    text: "About"
                    contentItem: Text {
                        text: parent.text
                        color: parent.checked ? root.textPrimary : root.textSecondary
                        font.bold: parent.checked
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: parent.checked ? root.bgSurface : "transparent"
                        border.color: parent.checked ? root.borderDark : "transparent"
                    }
                }
            }
        }

        // View Content Stack
        StackLayout {
            id: contentStack
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: navTabBar.currentIndex

            RegionsView {}
            HostingQueueView {}
            DownloadsView {}
            RegistryView {}
            SettingsView {}
            AboutView {}
        }
    }
}
