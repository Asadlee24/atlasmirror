#include "app_backend.h"
#include <QtCore/QDebug>
#include <QtCore/QFile>
#include <QtCore/QDir>
#include <QtCore/QJsonDocument>
#include <QtCore/QFileInfo>
#include <QtCore/QCryptographicHash>
#include <QtCore/QCoreApplication>
#include <QtCore/QMutexLocker>
#include <QtGui/QGuiApplication>
#include <QtGui/QClipboard>

AppBackend::AppBackend(QObject *parent)
    : QObject(parent)
{
    loadPredefinedCatalog();
    refreshIndex();
}

bool AppBackend::isCancelled(const QString &regionPath)
{
    QMutexLocker locker(&m_mutex);
    return m_cancelledRegions.contains(regionPath);
}

QJsonArray AppBackend::regions() const
{
    QMutexLocker locker(&m_mutex);
    return m_regions;
}

QJsonArray AppBackend::queue() const
{
    QMutexLocker locker(&m_mutex);
    return m_queue;
}

QJsonArray AppBackend::downloads() const
{
    QMutexLocker locker(&m_mutex);
    return m_downloads;
}

QJsonObject AppBackend::lastOperationResult() const
{
    QMutexLocker locker(&m_mutex);
    return m_lastResult;
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
    // Authoritative portable candidates without machine-specific paths
    QStringList candidatePaths = {
        "metadata/regions.json",
        "../metadata/regions.json",
        "../../metadata/regions.json",
        QCoreApplication::applicationDirPath() + "/metadata/regions.json",
        QCoreApplication::applicationDirPath() + "/../metadata/regions.json"
    };

    QByteArray catalogBytes;
    for (const QString &cp : candidatePaths) {
        QFile f(cp);
        if (f.open(QIODevice::ReadOnly)) {
            catalogBytes = f.readAll();
            break;
        }
    }

    QMutexLocker locker(&m_mutex);
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
    QMutexLocker locker(&m_mutex);
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
    QMutexLocker locker(&m_mutex);
    return m_queue;
}

QJsonArray AppBackend::getDownloadItems()
{
    QMutexLocker locker(&m_mutex);
    return m_downloads;
}

void AppBackend::refreshIndex()
{
    QThreadPool::globalInstance()->start([this]() {
        // Direct query to SDK without any CLI subprocess
        m_sdk.refreshOnChainRegistry();
        std::string jsonStr = m_sdk.discoverRegions();
        QJsonDocument doc = QJsonDocument::fromJson(QByteArray::fromStdString(jsonStr));

        QMetaObject::invokeMethod(this, [this, doc]() {
            QMutexLocker locker(&m_mutex);
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

            m_lastResult = QJsonObject{
                {"success", true},
                {"operation", "REFRESH_INDEX"},
                {"message", QString("Index refreshed via Core SDK. Loaded %1 regions.").arg(m_regions.size())}
            };
            emit regionsUpdated();
            emit operationResultChanged();
        }, Qt::QueuedConnection);
    });
}

void AppBackend::hostRegion(const QString &regionPath)
{
    {
        QMutexLocker locker(&m_mutex);
        m_cancelledRegions.remove(regionPath);

        // Remove old finished or failed entries for same region
        for (int i = 0; i < m_queue.size(); ++i) {
            QJsonObject obj = m_queue[i].toObject();
            if (obj["region"].toString() == regionPath) {
                QString st = obj["state"].toString();
                if (st == "PROCESSING" || st == "QUEUED") {
                    return;
                }
                m_queue.removeAt(i);
                break;
            }
        }

        QJsonObject item;
        item["region"] = regionPath;
        item["state"] = "QUEUED";
        item["progress"] = 0.0;
        item["error"] = "";
        m_queue.append(item);
    }
    emit queueUpdated();

    // Launch asynchronously on worker thread pool (prevents UI freeze)
    QThreadPool::globalInstance()->start([this, regionPath]() {
        if (isCancelled(regionPath)) {
            QMetaObject::invokeMethod(this, [this, regionPath]() {
                QMutexLocker locker(&m_mutex);
                for (int i = 0; i < m_queue.size(); ++i) {
                    QJsonObject obj = m_queue[i].toObject();
                    if (obj["region"].toString() == regionPath) {
                        obj["state"] = "CANCELLED";
                        m_queue[i] = obj;
                        break;
                    }
                }
                emit queueUpdated();
            }, Qt::QueuedConnection);
            return;
        }

        // Set to PROCESSING with preparation stage
        QMetaObject::invokeMethod(this, [this, regionPath]() {
            QMutexLocker locker(&m_mutex);
            for (int i = 0; i < m_queue.size(); ++i) {
                QJsonObject obj = m_queue[i].toObject();
                if (obj["region"].toString() == regionPath) {
                    obj["state"] = "PROCESSING";
                    obj["progress"] = 0.25;
                    m_queue[i] = obj;
                    break;
                }
            }
            emit queueUpdated();
        }, Qt::QueuedConnection);

        // Call direct SDK C++ implementation
        std::string resStr = m_sdk.hostRegion(regionPath.toStdString());
        QJsonDocument resDoc = QJsonDocument::fromJson(QByteArray::fromStdString(resStr));
        bool success = false;
        QString errMsg = "";
        QString cid = "";
        QString txHash = "";

        if (resDoc.isObject()) {
            QJsonObject resObj = resDoc.object();
            if (resObj.contains("cid") && !resObj["cid"].toString().isEmpty()) {
                cid = resObj["cid"].toString();
            }
            if (resObj.contains("tx_hash")) {
                txHash = resObj["tx_hash"].toString();
            }
            if (resObj.value("success").toBool() || (!cid.isEmpty() && !resObj.value("error").isString())) {
                success = true;
            } else {
                errMsg = resObj["message"].toString();
                if (errMsg.isEmpty()) errMsg = resObj["error"].toString();
            }
        }

        QMetaObject::invokeMethod(this, [this, regionPath, success, errMsg, cid, txHash]() {
            QMutexLocker locker(&m_mutex);
            if (m_cancelledRegions.contains(regionPath)) {
                for (int i = 0; i < m_queue.size(); ++i) {
                    QJsonObject obj = m_queue[i].toObject();
                    if (obj["region"].toString() == regionPath) {
                        obj["state"] = "CANCELLED";
                        m_queue[i] = obj;
                        break;
                    }
                }
                emit queueUpdated();
                return;
            }

            for (int i = 0; i < m_queue.size(); ++i) {
                QJsonObject obj = m_queue[i].toObject();
                if (obj["region"].toString() == regionPath) {
                    if (success) {
                        obj["state"] = "COMPLETE";
                        obj["progress"] = 1.0;
                        obj["error"] = "";
                        if (!txHash.isEmpty()) {
                            obj["tx_hash"] = txHash;
                        }
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
                        obj["progress"] = 0.0;
                        obj["error"] = errMsg.isEmpty() ? "Hosting failed" : errMsg;
                    }
                    m_queue[i] = obj;
                    emit queueUpdated();
                    break;
                }
            }

            m_lastResult = QJsonObject{
                {"success", success},
                {"operation", "HOST_REGION"},
                {"region", regionPath},
                {"cid", cid},
                {"tx_hash", txHash},
                {"error", errMsg}
            };
            emit operationResultChanged();
        }, Qt::QueuedConnection);
    });
}

void AppBackend::startBulkHost(const QJsonArray &regionPaths)
{
    if (regionPaths.isEmpty()) return;

    QStringList toHost;
    {
        QMutexLocker locker(&m_mutex);
        for (const QJsonValue &val : regionPaths) {
            QString reg = val.toString().trimmed();
            if (reg.isEmpty()) continue;
            toHost.append(reg);
            m_cancelledRegions.remove(reg);

            // Add or reset queue item
            bool exists = false;
            for (int i = 0; i < m_queue.size(); ++i) {
                QJsonObject obj = m_queue[i].toObject();
                if (obj["region"].toString() == reg) {
                    obj["state"] = "QUEUED";
                    obj["progress"] = 0.0;
                    obj["error"] = "";
                    m_queue[i] = obj;
                    exists = true;
                    break;
                }
            }
            if (!exists) {
                QJsonObject item;
                item["region"] = reg;
                item["state"] = "QUEUED";
                item["progress"] = 0.0;
                item["error"] = "";
                m_queue.append(item);
            }
        }
    }
    emit queueUpdated();

    // Asynchronously process bulk batch on worker thread
    QThreadPool::globalInstance()->start([this, toHost]() {
        // Construct batch records JSON payload
        QJsonArray recordsArr;
        for (const QString &r : toHost) {
            recordsArr.append(r);
        }
        QJsonDocument recordsDoc(recordsArr);
        std::string recordsStr = recordsDoc.toJson(QJsonDocument::Compact).toStdString();

        // Update items to PROCESSING
        QMetaObject::invokeMethod(this, [this, toHost]() {
            QMutexLocker locker(&m_mutex);
            for (const QString &r : toHost) {
                for (int i = 0; i < m_queue.size(); ++i) {
                    QJsonObject obj = m_queue[i].toObject();
                    if (obj["region"].toString() == r && obj["state"].toString() == "QUEUED") {
                        obj["state"] = "PROCESSING";
                        obj["progress"] = 0.3;
                        m_queue[i] = obj;
                        break;
                    }
                }
            }
            emit queueUpdated();
        }, Qt::QueuedConnection);

        // Execute batchRegister in C++ SDK
        std::string batchResStr = m_sdk.batchRegister(recordsStr);
        QJsonDocument bDoc = QJsonDocument::fromJson(QByteArray::fromStdString(batchResStr));
        bool success = false;
        QString txHash = "";
        QString errMsg = "";

        if (bDoc.isObject()) {
            QJsonObject bObj = bDoc.object();
            success = bObj.value("success").toBool();
            txHash = bObj.value("tx_hash").toString();
            if (!success) {
                errMsg = bObj.value("message").toString();
                if (errMsg.isEmpty()) errMsg = bObj.value("error").toString();
            }
        }

        // Refresh on-chain index
        m_sdk.refreshOnChainRegistry();

        QMetaObject::invokeMethod(this, [this, toHost, success, txHash, errMsg]() {
            QMutexLocker locker(&m_mutex);
            for (const QString &r : toHost) {
                for (int i = 0; i < m_queue.size(); ++i) {
                    QJsonObject obj = m_queue[i].toObject();
                    if (obj["region"].toString() == r) {
                        if (success) {
                            obj["state"] = "COMPLETE";
                            obj["progress"] = 1.0;
                            obj["error"] = "";
                            if (!txHash.isEmpty()) obj["tx_hash"] = txHash;
                            for (int j = 0; j < m_regions.size(); ++j) {
                                QJsonObject regObj = m_regions[j].toObject();
                                if (regObj["path"].toString() == r) {
                                    regObj["hosted"] = true;
                                    regObj["updateStatus"] = "UP_TO_DATE";
                                    m_regions[j] = regObj;
                                    break;
                                }
                            }
                        } else {
                            obj["state"] = "FAILED";
                            obj["progress"] = 0.0;
                            obj["error"] = errMsg.isEmpty() ? "Batch hosting failed" : errMsg;
                        }
                        m_queue[i] = obj;
                        break;
                    }
                }
            }
            emit queueUpdated();
            emit regionsUpdated();

            m_lastResult = QJsonObject{
                {"success", success},
                {"operation", "BATCH_REGISTER"},
                {"batch_size", static_cast<int>(toHost.size())},
                {"tx_hash", txHash},
                {"error", errMsg}
            };
            emit operationResultChanged();
        }, Qt::QueuedConnection);
    });
}

void AppBackend::cancelHost(const QString &regionPath)
{
    {
        QMutexLocker locker(&m_mutex);
        m_cancelledRegions.insert(regionPath);
        for (int i = 0; i < m_queue.size(); ++i) {
            QJsonObject obj = m_queue[i].toObject();
            if (obj["region"].toString() == regionPath) {
                obj["state"] = "CANCELLED";
                obj["progress"] = 0.0;
                obj["error"] = "Cancelled by user";
                m_queue[i] = obj;
                break;
            }
        }
    }
    emit queueUpdated();
}

void AppBackend::retryHost(const QString &regionPath)
{
    {
        QMutexLocker locker(&m_mutex);
        for (int i = 0; i < m_queue.size(); ++i) {
            QJsonObject obj = m_queue[i].toObject();
            if (obj["region"].toString() == regionPath) {
                m_queue.removeAt(i);
                break;
            }
        }
    }
    hostRegion(regionPath);
}

void AppBackend::clearCompletedQueue()
{
    QMutexLocker locker(&m_mutex);
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
    {
        QMutexLocker locker(&m_mutex);
        for (const QJsonValue &v : m_queue) {
            if (v.toObject()["state"].toString() == "FAILED") {
                failed.append(v.toObject()["region"].toString());
            }
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

    {
        QMutexLocker locker(&m_mutex);
        QJsonObject dl;
        dl["region"] = regionPath;
        dl["source"] = "Logos Storage / Canonical Geofabrik";
        dl["size"] = "Connecting...";
        dl["progress"] = 0.1;
        dl["status"] = "DOWNLOADING";
        m_downloads.append(dl);
    }
    emit downloadsUpdated();

    QThreadPool::globalInstance()->start([this, regionPath, destFile]() {
        // Direct SDK download with checksum verification and atomic rename on worker thread
        bool ok = m_sdk.downloadRegion(regionPath.toStdString(), destFile.toStdString());

        QMetaObject::invokeMethod(this, [this, regionPath, destFile, ok]() {
            QMutexLocker locker(&m_mutex);
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
                    break;
                }
            }
            emit downloadsUpdated();
        }, Qt::QueuedConnection);
    });
}

void AppBackend::copyToClipboard(const QString &text)
{
    QClipboard *cb = QGuiApplication::clipboard();
    if (cb) {
        cb->setText(text);
    }
    QMutexLocker locker(&m_mutex);
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
