#include "app_backend.h"
#include <QtCore/QDebug>
#include <QtCore/QFile>
#include <QtCore/QDir>
#include <QtCore/QJsonDocument>
#include <QtCore/QFileInfo>
#include <QtCore/QCryptographicHash>
#include <QtGui/QGuiApplication>
#include <QtGui/QClipboard>

AppBackend::AppBackend(QObject *parent)
    : QObject(parent)
{
    loadPredefinedCatalog();
    refreshIndex();
}

void AppBackend::setSearchFilter(const QString &filter)
{
    if (m_searchFilter != filter) {
        m_searchFilter = filter;
        emit searchFilterChanged();
    }
}

void AppBackend::setStatusFilter(const QString &filter)
{
    if (m_statusFilter != filter) {
        m_statusFilter = filter;
        emit statusFilterChanged();
    }
}

void AppBackend::setMaxConcurrency(int val)
{
    if (m_maxConcurrency != val && val > 0 && val <= 10) {
        m_maxConcurrency = val;
        emit maxConcurrencyChanged();
    }
}

void AppBackend::setTelemetryEnabled(bool val)
{
    if (m_telemetryEnabled != val) {
        m_telemetryEnabled = val;
        emit telemetryEnabledChanged();
    }
}

void AppBackend::loadPredefinedCatalog()
{
    // Try to load metadata/regions.json from working directory or relative path
    QStringList candidatePaths = {
        "metadata/regions.json",
        "../metadata/regions.json",
        "../../metadata/regions.json",
        "/mnt/c/Users/Aftab/Desktop/atlasmirror/metadata/regions.json"
    };

    QByteArray catalogBytes;
    for (const QString &cp : candidatePaths) {
        QFile f(cp);
        if (f.open(QIODevice::ReadOnly)) {
            catalogBytes = f.readAll();
            break;
        }
    }

    m_regions = QJsonArray();

    if (!catalogBytes.isEmpty()) {
        QJsonDocument doc = QJsonDocument::fromJson(catalogBytes);
        if (doc.isObject() && doc.object().contains("regions")) {
            QJsonArray arr = doc.object()["regions"].toArray();
            for (const QJsonValue &val : arr) {
                QJsonObject r = val.toObject();
                r["hosted"] = false;
                r["cid"] = "—";
                r["checksum"] = "—";
                r["version"] = "—";
                r["updateStatus"] = "NOT_HOSTED";
                m_regions.append(r);
            }
        }
    }

    // Closed-set 72 regions baseline default if regions.json is unavailable
    if (m_regions.isEmpty()) {
        QStringList allPaths = {
            "asia/pakistan", "europe/germany", "europe/france", "europe/great-britain",
            "europe/italy", "europe/spain", "europe/poland", "europe/netherlands",
            "europe/belgium", "europe/switzerland", "europe/austria", "europe/czech-republic",
            "europe/sweden", "europe/norway", "europe/denmark", "europe/finland",
            "europe/portugal", "europe/greece", "europe/ireland-and-northern-ireland",
            "europe/hungary", "europe/romania", "europe/bulgaria", "europe/ukraine",
            "europe/belarus", "europe/turkey", "north-america/canada", "north-america/mexico",
            "asia/japan", "asia/south-korea", "asia/indonesia", "asia/thailand",
            "asia/vietnam", "asia/malaysia-singapore-brunei", "asia/philippines",
            "asia/bangladesh", "asia/iran", "australia-oceania/australia",
            "south-america/brazil", "south-america/argentina", "south-america/colombia",
            "south-america/peru", "south-america/chile", "africa/south-africa",
            "africa/egypt", "africa/nigeria", "africa/kenya", "africa/morocco", "africa/ethiopia",
            "us/california", "us/texas", "us/florida", "us/new-york", "us/washington",
            "us/illinois", "us/georgia", "us/pennsylvania",
            "india/central-zone", "india/eastern-zone", "india/north-eastern-zone",
            "india/northern-zone", "india/southern-zone", "india/western-zone",
            "china/guangdong", "china/jiangsu", "china/shandong", "china/zhejiang",
            "china/sichuan", "china/henan",
            "russia/central-fed-district", "russia/northwestern-fed-district",
            "russia/volga-fed-district", "russia/siberian-fed-district"
        };

        for (const QString &p : allPaths) {
            QJsonObject r;
            r["path"] = p;
            QStringList parts = p.split('/');
            QString prefix = parts.value(0);
            QString suffix = parts.value(1, p);
            if (prefix == "us" || prefix == "india" || prefix == "china" || prefix == "russia") {
                r["level"] = "subregion";
                r["parent"] = prefix;
            } else {
                r["level"] = "country";
                r["parent"] = QJsonValue::Null;
            }
            r["name"] = suffix;
            r["hosted"] = false;
            r["cid"] = "—";
            r["checksum"] = "—";
            r["version"] = "—";
            r["updateStatus"] = "NOT_HOSTED";
            r["geofabrik_url"] = "https://download.geofabrik.de/" + p + "-latest.osm.pbf";
            r["md5_url"] = "https://download.geofabrik.de/" + p + "-latest.osm.pbf.md5";
            m_regions.append(r);
        }
    }
}

QJsonArray AppBackend::getFilteredRegions()
{
    QJsonArray res;
    QString search = m_searchFilter.trimmed().toLower();
    QString status = m_statusFilter.toUpper();

    for (const QJsonValue &v : m_regions) {
        QJsonObject obj = v.toObject();
        QString path = obj["path"].toString().toLower();
        QString name = obj["name"].toString().toLower();
        bool hosted = obj["hosted"].toBool();
        QString updateStatus = obj["updateStatus"].toString();

        if (!search.isEmpty() && !path.contains(search) && !name.contains(search)) {
            continue;
        }

        if (status == "HOSTED" && !hosted) continue;
        if (status == "NOT HOSTED" && hosted) continue;
        if (status == "UPDATE AVAILABLE" && updateStatus != "UPDATE_AVAILABLE") continue;

        res.append(obj);
    }
    return res;
}

QJsonArray AppBackend::getQueueItems()
{
    return m_queue;
}

QJsonArray AppBackend::getDownloadItems()
{
    return m_downloads;
}

void AppBackend::refreshIndex()
{
    // Truthful direct query to SDK without any CLI subprocess
    m_sdk.refreshOnChainRegistry();
    std::string jsonStr = m_sdk.discoverRegions();
    QJsonDocument doc = QJsonDocument::fromJson(QByteArray::fromStdString(jsonStr));

    if (doc.isArray()) {
        QJsonArray liveList = doc.array();
        for (const QJsonValue &lv : liveList) {
            QJsonObject lObj = lv.toObject();
            QString lPath = lObj["path"].toString();
            for (int i = 0; i < m_regions.size(); ++i) {
                QJsonObject r = m_regions[i].toObject();
                if (r["path"].toString() == lPath) {
                    bool isHosted = lObj["hosted"].toBool();
                    r["hosted"] = isHosted;
                    if (isHosted) {
                        r["cid"] = lObj["cid"].toString();
                        r["checksum"] = lObj["checksum"].toString();
                        r["version"] = lObj["version"].toString();
                        r["updateStatus"] = "UP_TO_DATE";
                    } else {
                        r["hosted"] = false;
                        r["cid"] = "—";
                        r["checksum"] = "—";
                        r["version"] = "—";
                        r["updateStatus"] = "NOT_HOSTED";
                    }
                    m_regions[i] = r;
                    break;
                }
            }
        }
    }

    emit regionsUpdated();

    m_lastResult = QJsonObject{
        {"success", true},
        {"operation", "REFRESH_INDEX"},
        {"message", QString("Index refreshed via Core SDK. Loaded %1 regions.").arg(m_regions.size())}
    };
    emit operationResultChanged();
}

void AppBackend::hostRegion(const QString &regionPath)
{
    QJsonObject item;
    item["region"] = regionPath;
    item["state"] = "PROCESSING";
    item["progress"] = 0.5;
    item["error"] = "";
    m_queue.append(item);
    emit queueUpdated();

    // Call SDK directly
    std::string resStr = m_sdk.hostRegion(regionPath.toStdString());
    QJsonDocument resDoc = QJsonDocument::fromJson(QByteArray::fromStdString(resStr));
    bool success = false;
    QString errMsg = "";
    QString cid = "";

    if (resDoc.isObject()) {
        QJsonObject resObj = resDoc.object();
        if (resObj.contains("cid") && !resObj["cid"].toString().isEmpty()) {
            success = true;
            cid = resObj["cid"].toString();
        } else if (resObj["success"].toBool()) {
            success = true;
        } else {
            errMsg = resObj["message"].toString();
            if (errMsg.isEmpty()) errMsg = resObj["error"].toString();
        }
    }

    for (int i = 0; i < m_queue.size(); ++i) {
        QJsonObject obj = m_queue[i].toObject();
        if (obj["region"].toString() == regionPath) {
            if (success) {
                obj["state"] = "COMPLETE";
                obj["progress"] = 1.0;
                obj["error"] = "";
                for (int j = 0; j < m_regions.size(); ++j) {
                    QJsonObject r = m_regions[j].toObject();
                    if (r["path"].toString() == regionPath) {
                        r["hosted"] = true;
                        if (!cid.isEmpty()) r["cid"] = cid;
                        r["updateStatus"] = "UP_TO_DATE";
                        m_regions[j] = r;
                        break;
                    }
                }
                emit regionsUpdated();
            } else {
                obj["state"] = "FAILED";
                obj["error"] = errMsg.isEmpty() ? "Hosting failed" : errMsg;
            }
            m_queue[i] = obj;
            emit queueUpdated();
            break;
        }
    }
}

void AppBackend::startBulkHost(const QJsonArray &regionPaths)
{
    if (regionPaths.isEmpty()) return;

    for (const QJsonValue &val : regionPaths) {
        QString reg = val.toString();
        hostRegion(reg);
    }
}

void AppBackend::cancelHost(const QString &regionPath)
{
    for (int i = 0; i < m_queue.size(); ++i) {
        QJsonObject obj = m_queue[i].toObject();
        if (obj["region"].toString() == regionPath) {
            obj["state"] = "CANCELLED";
            m_queue[i] = obj;
            emit queueUpdated();
            break;
        }
    }
}

void AppBackend::retryHost(const QString &regionPath)
{
    for (int i = 0; i < m_queue.size(); ++i) {
        QJsonObject obj = m_queue[i].toObject();
        if (obj["region"].toString() == regionPath) {
            m_queue.removeAt(i);
            break;
        }
    }
    hostRegion(regionPath);
}

void AppBackend::clearCompletedQueue()
{
    QJsonArray newQueue;
    for (const QJsonValue &v : m_queue) {
        QString st = v.toObject()["state"].toString();
        if (st != "COMPLETE" && st != "CANCELLED") {
            newQueue.append(v);
        }
    }
    m_queue = newQueue;
    emit queueUpdated();
}

void AppBackend::retryAllFailed()
{
    QStringList failed;
    for (const QJsonValue &v : m_queue) {
        if (v.toObject()["state"].toString() == "FAILED") {
            failed.append(v.toObject()["region"].toString());
        }
    }
    clearCompletedQueue();
    for (const QString &r : failed) {
        hostRegion(r);
    }
}

void AppBackend::startDownload(const QString &regionPath)
{
    QString destDir = "./downloads";
    QDir().mkpath(destDir);
    QString cleanName = QString(regionPath).replace('/', '_');
    QString destFile = QString("%1/%2-latest.osm.pbf").arg(destDir, cleanName);

    QJsonObject dl;
    dl["region"] = regionPath;
    dl["source"] = "Logos Storage / Canonical Geofabrik";
    dl["size"] = "Downloading...";
    dl["progress"] = 0.5;
    dl["status"] = "DOWNLOADING";
    m_downloads.append(dl);
    emit downloadsUpdated();

    // Direct SDK download with checksum verification and atomic rename
    bool ok = m_sdk.downloadRegion(regionPath.toStdString(), destFile.toStdString());

    for (int i = 0; i < m_downloads.size(); ++i) {
        QJsonObject obj = m_downloads[i].toObject();
        if (obj["region"].toString() == regionPath) {
            if (ok && QFile::exists(destFile)) {
                qint64 sz = QFileInfo(destFile).size();
                obj["size"] = QString("%1 MB").arg(sz / (1024 * 1024));
                obj["progress"] = 1.0;
                obj["status"] = "VERIFIED";
            } else {
                obj["status"] = "FAILED";
                obj["progress"] = 0.0;
            }
            m_downloads[i] = obj;
            emit downloadsUpdated();
            break;
        }
    }
}

void AppBackend::copyToClipboard(const QString &text)
{
    QClipboard *cb = QGuiApplication::clipboard();
    if (cb) {
        cb->setText(text);
    }
    m_lastResult = QJsonObject{
        {"success", true},
        {"operation", "COPY_CID"},
        {"message", QString("Copied to clipboard: %1").arg(text)}
    };
    emit operationResultChanged();
}

QString AppBackend::queryRegistry(const QString &queryType, const QString &queryValue)
{
    std::string res;
    if (queryType.contains("CID", Qt::CaseInsensitive)) {
        res = m_sdk.getByCid(queryValue.toStdString());
    } else if (queryType.contains("Parent", Qt::CaseInsensitive)) {
        res = m_sdk.getChildren(queryValue.toStdString());
    } else {
        res = m_sdk.resolveRegion(queryValue.toStdString());
    }
    return QString::fromStdString(res);
}

QString AppBackend::importLocal(const QString &regionPath, const QString &localFilePath)
{
    QString cleanPath = localFilePath;
    if (cleanPath.startsWith("file:///")) {
#ifdef Q_OS_WIN
        cleanPath = cleanPath.mid(8);
#else
        cleanPath = cleanPath.mid(7);
#endif
    } else if (cleanPath.startsWith("file://")) {
        cleanPath = cleanPath.mid(7);
    }

    std::string res = m_sdk.importLocal(regionPath.toStdString(), cleanPath.toStdString());
    return QString::fromStdString(res);
}

QString AppBackend::updateCheck(const QString &regionPath)
{
    std::string res = m_sdk.checkUpdate(regionPath.toStdString());
    return QString::fromStdString(res);
}
