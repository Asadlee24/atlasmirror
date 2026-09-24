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

        readonly property var cBackend: (typeof appBackend !== "undefined" && appBackend) ? appBackend : null

        function refreshIndex() {
            if (cBackend) cBackend.refreshIndex();
        }

        function hostRegion(path) {
            if (cBackend) cBackend.hostRegion(path);
        }

        function startBulkHost(paths) {
            if (cBackend) cBackend.startBulkHost(paths);
        }

        function cancelHost(path) {
            if (cBackend) cBackend.cancelHost(path);
        }

        function retryHost(path) {
            if (cBackend) cBackend.retryHost(path);
        }

        function clearCompletedQueue() {
            if (cBackend) cBackend.clearCompletedQueue();
        }

        function retryAllFailed() {
            if (cBackend) cBackend.retryAllFailed();
        }

        function startDownload(path) {
            if (cBackend) cBackend.startDownload(path);
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
