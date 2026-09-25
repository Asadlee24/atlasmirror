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

        readonly property var defaultRegions: [
            {"path": "asia/pakistan", "name": "Pakistan", "level": "Country", "parent": "", "hosted": true, "cid": "zDvZRwzmb2rhmbuKmxifz7mCY9PgRtFJUwyescB3xfCKzSvE61vz", "checksum": "5dd3c567f557b843aef1576b8973f81f", "version": "2026-09-24", "updateStatus": "UP_TO_DATE"},
            {"path": "china/henan", "name": "Henan", "level": "Subregion", "parent": "china", "hosted": true, "cid": "zDvZRwzmb2rhXLBiRXtyd74Y8MB29es8si7ZEuHL6oMBuaLQyC88", "checksum": "765edcbf39256eace4fe32828a14cc58", "version": "2026-09-24", "updateStatus": "UP_TO_DATE"},
            {"path": "europe/germany", "name": "Germany", "level": "Country", "parent": "", "hosted": false, "cid": "—", "checksum": "—", "version": "—", "updateStatus": "NOT_HOSTED"},
            {"path": "us/california", "name": "California", "level": "Subregion", "parent": "us", "hosted": false, "cid": "—", "checksum": "—", "version": "—", "updateStatus": "NOT_HOSTED"}
        ]

        property var regions: (cBackend && cBackend.regions && cBackend.regions.length > 0) ? cBackend.regions : defaultRegions
        property var queue: (cBackend && cBackend.queue) ? cBackend.queue : []
        property var downloads: (cBackend && cBackend.downloads) ? cBackend.downloads : []

        signal regionsUpdated()
        signal queueUpdated()
        signal downloadsUpdated()

        Component.onCompleted: {
            if (cBackend) {
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
            if (cBackend) cBackend.refreshIndex();
        }

        function hostRegion(path) {
            if (cBackend) {
                cBackend.hostRegion(path);
            } else {
                var q = (backend.queue || []).slice();
                q.unshift({
                    "path": path,
                    "status": "PROCESSING",
                    "step": "Publishing to Logos Storage & LEZ Registry...",
                    "progress": 55,
                    "cid": "zDvZRwzm" + Math.random().toString(36).substring(2, 10),
                    "canRetry": false,
                    "canCancel": true
                });
                backend.queue = q;
                backend.queueUpdated();
            }
        }

        function startBulkHost(paths) {
            if (cBackend) {
                cBackend.startBulkHost(paths);
            } else {
                for (var i = 0; i < paths.length; i++) {
                    hostRegion(paths[i]);
                }
            }
        }

        function cancelHost(path) {
            if (cBackend) {
                cBackend.cancelHost(path);
            } else {
                var q = (backend.queue || []).filter(function(item) { return item.path !== path; });
                backend.queue = q;
                backend.queueUpdated();
            }
        }

        function retryHost(path) {
            if (cBackend) cBackend.retryHost(path);
        }

        function clearCompletedQueue() {
            if (cBackend) {
                cBackend.clearCompletedQueue();
            } else {
                backend.queue = [];
                backend.queueUpdated();
            }
        }

        function retryAllFailed() {
            if (cBackend) cBackend.retryAllFailed();
        }

        function startDownload(path) {
            if (cBackend) {
                cBackend.startDownload(path);
            } else {
                var d = (backend.downloads || []).slice();
                d.unshift({
                    "path": path,
                    "status": "DOWNLOADING",
                    "progress": 48,
                    "cid": "zDvZRwzm...",
                    "retrievedBytes": 23592960,
                    "totalBytes": 49137459,
                    "speed": "2.8 MB/s"
                });
                backend.downloads = d;
                backend.downloadsUpdated();
            }
        }

        function openDownloadDir() {
            if (cBackend && cBackend.openDownloadDir) cBackend.openDownloadDir();
        }

        function copyToClipboard(text) {
            if (cBackend) cBackend.copyToClipboard(text);
        }

        function queryRegistry(type, val) {
            return cBackend ? cBackend.queryRegistry(type, val) : "";
        }

        function importLocal(path, file) {
            return cBackend ? cBackend.importLocal(path, file) : "";
        }

        function updateCheck(path) {
            return cBackend ? cBackend.updateCheck(path) : "";
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
