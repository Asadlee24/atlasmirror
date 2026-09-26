import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: regionsView

    // Full 72 closed-set catalog data
    readonly property var allCatalogRegions: [
        { path: "asia/pakistan", name: "Pakistan", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "china/henan", name: "Henan", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "africa/ethiopia", name: "Ethiopia", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/bulgaria", name: "Bulgaria", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "africa/egypt", name: "Egypt", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "asia/iran", name: "Iran", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "africa/morocco", name: "Morocco", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "asia/malaysia-singapore-brunei", name: "Malaysia-Singapore-Brunei", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "china/shandong", name: "Shandong", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "china/jiangsu", name: "Jiangsu", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "china/zhejiang", name: "Zhejiang", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "china/sichuan", name: "Sichuan", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "india/north-eastern-zone", name: "North-Eastern Zone", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "china/guangdong", name: "Guangdong", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "india/western-zone", name: "Western Zone", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "india/northern-zone", name: "Northern Zone", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "india/eastern-zone", name: "Eastern Zone", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "south-america/peru", name: "Peru", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "asia/south-korea", name: "South Korea", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/hungary", name: "Hungary", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "asia/thailand", name: "Thailand", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/romania", name: "Romania", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "asia/vietnam", name: "Vietnam", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "south-america/colombia", name: "Colombia", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/greece", name: "Greece", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/germany", name: "Germany", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/france", name: "France", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/great-britain", name: "United Kingdom", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/italy", name: "Italy", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/spain", name: "Spain", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/poland", name: "Poland", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/netherlands", name: "Netherlands", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/belgium", name: "Belgium", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/switzerland", name: "Switzerland", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/austria", name: "Austria", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/czech-republic", name: "Czech Republic", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/sweden", name: "Sweden", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/norway", name: "Norway", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/denmark", name: "Denmark", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/finland", name: "Finland", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/portugal", name: "Portugal", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/ireland-and-northern-ireland", name: "Ireland", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/ukraine", name: "Ukraine", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/belarus", name: "Belarus", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "europe/turkey", name: "Turkey", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "north-america/canada", name: "Canada", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "north-america/mexico", name: "Mexico", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "asia/japan", name: "Japan", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "asia/indonesia", name: "Indonesia", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "asia/philippines", name: "Philippines", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "asia/bangladesh", name: "Bangladesh", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "australia-oceania/australia", name: "Australia", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "south-america/brazil", name: "Brazil", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "south-america/argentina", name: "Argentina", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "south-america/chile", name: "Chile", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "africa/south-africa", name: "South Africa", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "africa/nigeria", name: "Nigeria", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "africa/kenya", name: "Kenya", level: "country", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "us/california", name: "California", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "us/texas", name: "Texas", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "us/florida", name: "Florida", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "us/new-york", name: "New York", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "us/washington", name: "Washington", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "us/illinois", name: "Illinois", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "us/georgia", name: "Georgia", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "us/pennsylvania", name: "Pennsylvania", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "india/central-zone", name: "Central Zone", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "india/southern-zone", name: "Southern Zone", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "russia/central-fed-district", name: "Central Federal District", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "russia/northwestern-fed-district", name: "Northwestern Federal District", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "russia/volga-fed-district", name: "Volga Federal District", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" },
        { path: "russia/siberian-fed-district", name: "Siberian Federal District", level: "subregion", version: "—", hosted: false, cid: "—", checksum: "—", updateStatus: "NOT_HOSTED" }
    ]

    ListModel {
        id: regionsModel
    }

    Connections {
        target: (typeof backend !== "undefined") ? backend : null
        function onRegionsUpdated() {
            populateModel()
        }
    }

    FileDialog {
        id: importFileDialog
        title: "Select Local .osm.pbf File to Import"
        nameFilters: ["OSM PBF files (*.osm.pbf *.pbf)", "All files (*)"]
        onAccepted: {
            var pathStr = currentFile ? currentFile.toString() : selectedFile.toString()
            if (typeof backend !== "undefined" && backend.importLocal && selectedItem) {
                var resStr = backend.importLocal(selectedItem.path, pathStr)
                try {
                    var resObj = JSON.parse(resStr)
                    if (resObj.success) {
                        statusNotification = "Successfully imported " + selectedItem.path + " (MD5: " + (resObj.computed_md5 || "verified") + ")"
                        populateModel()
                    } else {
                        statusNotification = "Import failed for " + selectedItem.path + ": " + (resObj.error || resObj.message || "Unknown error")
                    }
                } catch(e) {
                    statusNotification = "Import result: " + resStr
                }
            }
        }
    }

    Component.onCompleted: {
        populateModel()
    }

    function populateModel() {
        regionsModel.clear()
        var s = (typeof searchField !== "undefined" && searchField) ? searchField.text.trim().toLowerCase() : ""
        var f = (typeof filterCombo !== "undefined" && filterCombo) ? filterCombo.currentText : "All"

        var sourceList = allCatalogRegions
        if (typeof backend !== "undefined" && backend.regions && backend.regions.length > 0) {
            sourceList = backend.regions
        }

        for (var i = 0; i < sourceList.length; ++i) {
            var item = sourceList[i]
            var p = item.path || ""
            var n = item.name || p
            var pathMatch = s === "" || p.toLowerCase().indexOf(s) !== -1 || n.toLowerCase().indexOf(s) !== -1
            if (!pathMatch) continue

            var isHosted = !!item.hosted
            var updateSt = item.updateStatus || (isHosted ? "UP_TO_DATE" : "NOT_HOSTED")

            if (f === "Hosted" && !isHosted) continue
            if (f === "Not hosted" && isHosted) continue
            if (f === "Update available" && updateSt !== "UPDATE_AVAILABLE") continue

            regionsModel.append({
                path: p,
                name: n,
                level: item.level || "country",
                version: item.version || "—",
                hosted: isHosted,
                cid: item.cid || "—",
                checksum: item.checksum || "—",
                updateStatus: updateSt
            })
        }
    }

    property var selectedItem: null
    property string statusNotification: ""

    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        // Left: Table & Controls
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12

            // Status Banner if notification exists
            Rectangle {
                visible: statusNotification !== ""
                Layout.fillWidth: true
                Layout.preferredHeight: 32
                color: "#1E3A1E"
                border.color: "#4CAF50"
                radius: 4

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    Text {
                        text: statusNotification
                        color: "#81C784"
                        font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: "✖"
                        onClicked: statusNotification = ""
                    }
                }
            }

            // Filter Bar
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                TextField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholderText: "Search region by path or name (72 regions available)..."
                    color: "#FFFFFF"
                    background: Rectangle {
                        color: "#111111"
                        border.color: "#333333"
                        radius: 2
                    }
                    onTextChanged: populateModel()
                }

                ComboBox {
                    id: filterCombo
                    model: ["All", "Hosted", "Not hosted", "Update available"]
                    background: Rectangle {
                        color: "#111111"
                        border.color: "#333333"
                        radius: 2
                    }
                    onCurrentTextChanged: populateModel()
                }

                Button {
                    text: "Refresh Index"
                    onClicked: {
                        if (typeof backend !== "undefined" && backend.refreshIndex) {
                            backend.refreshIndex()
                        }
                        statusNotification = "Refreshed live LEZ on-chain registry state. 72 regions loaded."
                        populateModel()
                    }
                }

                Button {
                    text: "Batch Host (25)"
                    onClicked: {
                        var batchList = []
                        for (var i = 0; i < allCatalogRegions.length; ++i) {
                            if (!allCatalogRegions[i].hosted) {
                                batchList.push(allCatalogRegions[i].path)
                                if (batchList.length >= 25) break
                            }
                        }
                        if (typeof backend !== "undefined" && backend.startBulkHost) {
                            backend.startBulkHost(batchList)
                        }
                        statusNotification = "Queued " + batchList.length + " regions for batch hosting."
                    }
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

                    Text { text: "Region"; color: "#AAAAAA"; font.bold: true; Layout.preferredWidth: 220 }
                    Text { text: "Level"; color: "#AAAAAA"; font.bold: true; Layout.preferredWidth: 90 }
                    Text { text: "Version"; color: "#AAAAAA"; font.bold: true; Layout.preferredWidth: 95 }
                    Text { text: "Storage Status"; color: "#AAAAAA"; font.bold: true; Layout.preferredWidth: 110 }
                    Text { text: "CID / Source"; color: "#AAAAAA"; font.bold: true; Layout.fillWidth: true }
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
                    height: 42
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

                        Text { text: model.path; color: "#FFFFFF"; font.family: "monospace"; Layout.preferredWidth: 220; elide: Text.ElideRight }
                        Text { text: model.level; color: "#888888"; Layout.preferredWidth: 90 }
                        Text { text: model.version; color: "#888888"; Layout.preferredWidth: 95 }
                        Text {
                            text: model.hosted ? "Hosted" : "Not hosted"
                            color: model.hosted ? "#4CAF50" : "#888888"
                            font.bold: true
                            Layout.preferredWidth: 110
                        }
                        Text {
                            text: model.hosted ? model.cid : "Geofabrik Fallback"
                            color: model.hosted ? "#81D4FA" : "#666666"
                            font.family: "monospace"
                            elide: Text.ElideMiddle
                            Layout.fillWidth: true
                        }
                        Button {
                            text: model.hosted ? "Download" : "Host"
                            Layout.preferredWidth: 90
                            onClicked: {
                                selectedItem = model
                                if (model.hosted) {
                                    if (typeof backend !== "undefined" && backend.startDownload) {
                                        backend.startDownload(model.path)
                                    }
                                    statusNotification = "Initiated download for " + model.path + " via Logos Storage."
                                } else {
                                    if (typeof backend !== "undefined" && backend.hostRegion) {
                                        backend.hostRegion(model.path)
                                    }
                                    statusNotification = "Queued " + model.path + " for Logos Storage hosting."
                                }
                            }
                        }
                    }
                }
            }
        }

        // Right: Inspector Panel
        Rectangle {
            Layout.preferredWidth: 340
            Layout.fillHeight: true
            color: "#111111"
            border.color: "#222222"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                Text {
                    text: "Region Inspector"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#FFFFFF"
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: "#222222" }

                Text { text: "Canonical Path:"; color: "#888888"; font.pixelSize: 12 }
                Text { text: selectedItem ? selectedItem.path : "Select a region"; color: "#FFFFFF"; font.family: "monospace"; font.bold: true }

                Text { text: "Hierarchy Level:"; color: "#888888"; font.pixelSize: 12 }
                Text { text: selectedItem ? selectedItem.level : "—"; color: "#FFFFFF" }

                Text { text: "Logos Storage CID:"; color: "#888888"; font.pixelSize: 12 }
                Text {
                    text: selectedItem ? selectedItem.cid : "—"
                    color: (selectedItem && selectedItem.hosted) ? "#81D4FA" : "#888888"
                    font.family: "monospace"
                    wrapMode: Text.WrapAnywhere
                    Layout.fillWidth: true
                }

                Text { text: "MD5 Checksum (Published):"; color: "#888888"; font.pixelSize: 12 }
                Text {
                    text: selectedItem ? selectedItem.checksum : "—"
                    color: "#A5D6A7"
                    font.family: "monospace"
                    Layout.fillWidth: true
                }

                Text { text: "Verified Version:"; color: "#888888"; font.pixelSize: 12 }
                Text { text: selectedItem ? selectedItem.version : "—"; color: "#FFFFFF" }

                Text { text: "Registry State:"; color: "#888888"; font.pixelSize: 12 }
                Text {
                    text: (selectedItem && selectedItem.hosted) ? "VERIFIED ON TESTNET 0.3" : "READY TO HOST"
                    color: (selectedItem && selectedItem.hosted) ? "#4CAF50" : "#FFB74D"
                    font.bold: true
                }

                Item { Layout.fillHeight: true }

                // Action Buttons
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Button {
                            text: "Copy CID"
                            Layout.fillWidth: true
                            enabled: selectedItem && selectedItem.hosted && selectedItem.cid !== "—"
                            onClicked: {
                                if (typeof backend !== "undefined" && backend.copyToClipboard) {
                                    backend.copyToClipboard(selectedItem.cid)
                                }
                                statusNotification = "CID copied to clipboard: " + selectedItem.cid
                            }
                        }

                        Button {
                            text: "Check Update"
                            Layout.fillWidth: true
                            enabled: selectedItem !== null
                            onClicked: {
                                if (typeof backend !== "undefined" && backend.updateCheck) {
                                    var res = backend.updateCheck(selectedItem.path)
                                    try {
                                        var obj = JSON.parse(res)
                                        var st = obj.status || "UNKNOWN"
                                        statusNotification = "Update check for " + selectedItem.path + ": " + st
                                    } catch(e) {
                                        statusNotification = "Update check: " + res
                                    }
                                } else {
                                    statusNotification = "Backend unavailable for update check."
                                }
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Button {
                            text: selectedItem && selectedItem.hosted ? "Download PBF" : "Host Region"
                            Layout.fillWidth: true
                            enabled: selectedItem !== null
                            onClicked: {
                                if (selectedItem.hosted) {
                                    if (typeof backend !== "undefined" && backend.startDownload) {
                                        backend.startDownload(selectedItem.path)
                                    }
                                    statusNotification = "Started download for " + selectedItem.path
                                } else {
                                    if (typeof backend !== "undefined" && backend.hostRegion) {
                                        backend.hostRegion(selectedItem.path)
                                    }
                                    statusNotification = "Hosting pipeline started for " + selectedItem.path
                                }
                            }
                        }

                        Button {
                            text: "Import Local"
                            Layout.fillWidth: true
                            enabled: selectedItem !== null
                            onClicked: {
                                importFileDialog.open()
                            }
                        }
                    }
                }
            }
        }
    }
}
