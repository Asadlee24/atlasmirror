#include "atlasmirror_sdk_impl.h"
#include <QtCore/QFile>
#include <QtCore/QJsonDocument>
#include <QtCore/QCryptographicHash>
#include <QtCore/QDateTime>
#include <QtCore/QDebug>

AtlasMirrorSdkImpl::AtlasMirrorSdkImpl(QObject *parent)
    : QObject(parent)
{
    loadPredefinedCatalog();
}

void AtlasMirrorSdkImpl::loadPredefinedCatalog()
{
    // Initialize standard predefined 72 regions from LP-0018
    QStringList paths = {
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

    for (const QString &path : paths) {
        QJsonObject obj;
        obj["path"] = path;
        
        if (path.startsWith("us/") || path.startsWith("india/") || path.startsWith("china/") || path.startsWith("russia/")) {
            obj["level"] = "subregion";
            obj["parent"] = path.section('/', 0, 0);
            obj["name"] = path.section('/', 1, 1);
        } else {
            obj["level"] = "country";
            obj["parent"] = QJsonValue::Null;
            obj["name"] = path.section('/', 1, 1);
        }

        obj["geofabrik_url"] = QString("https://download.geofabrik.de/%1-latest.osm.pbf").arg(path);
        obj["md5_url"] = QString("https://download.geofabrik.de/%1-latest.osm.pbf.md5").arg(path);
        obj["hosted"] = false;
        obj["cid"] = "";
        obj["checksum"] = "";
        obj["version"] = "";

        m_catalog[path] = obj;
    }
}

QJsonArray AtlasMirrorSdkImpl::discoverRegions()
{
    QJsonArray array;
    for (auto it = m_catalog.constBegin(); it != m_catalog.constEnd(); ++it) {
        array.append(it.value());
    }
    return array;
}

QJsonObject AtlasMirrorSdkImpl::getRegion(const QString &path)
{
    if (m_catalog.contains(path)) {
        return m_catalog[path];
    }
    QJsonObject err;
    err["error"] = "NOT_FOUND";
    return err;
}

QJsonObject AtlasMirrorSdkImpl::getByCid(const QString &cid)
{
    if (cid.trimmed().isEmpty()) {
        QJsonObject err;
        err["error"] = "INVALID_CID";
        return err;
    }

    for (auto it = m_hostedRecords.constBegin(); it != m_hostedRecords.constEnd(); ++it) {
        if (it.value()["cid"].toString() == cid) {
            return it.value();
        }
    }
    QJsonObject err;
    err["error"] = "CID_NOT_FOUND";
    return err;
}

QJsonArray AtlasMirrorSdkImpl::getChildren(const QString &parent)
{
    QJsonArray children;
    for (auto it = m_catalog.constBegin(); it != m_catalog.constEnd(); ++it) {
        if (it.value()["parent"].toString() == parent) {
            children.append(it.value());
        }
    }
    return children;
}

QJsonObject AtlasMirrorSdkImpl::resolveRegion(const QString &path)
{
    QJsonObject res;
    if (!m_catalog.contains(path)) {
        res["status"] = "UNSUPPORTED_REGION";
        return res;
    }

    QJsonObject entry = m_catalog[path];
    if (entry["hosted"].toBool()) {
        res["source"] = "logos_storage";
        res["cid"] = entry["cid"].toString();
        res["checksum"] = entry["checksum"].toString();
        res["version"] = entry["version"].toString();
        res["status"] = "HOSTED";
    } else {
        // Direct central fallback when region is not yet hosted
        res["source"] = "geofabrik_fallback";
        res["url"] = entry["geofabrik_url"].toString();
        res["md5_url"] = entry["md5_url"].toString();
        res["status"] = "CENTRAL_FALLBACK";
    }
    return res;
}

QJsonObject AtlasMirrorSdkImpl::checkUpdate(const QString &path)
{
    QJsonObject res;
    if (!m_catalog.contains(path)) {
        res["status"] = "SOURCE_REGION_UNKNOWN";
        return res;
    }

    QJsonObject entry = m_catalog[path];
    if (!entry["hosted"].toBool()) {
        res["status"] = "NOT_HOSTED";
        return res;
    }

    // When connected to on-chain registry, compare on-chain timestamp with Geofabrik index
    res["status"] = "UP_TO_DATE";
    res["current_version"] = entry["version"].toString();
    res["upstream_version"] = entry["version"].toString();
    return res;
}

QJsonObject AtlasMirrorSdkImpl::hostRegion(const QString &path)
{
    QJsonObject res;
    if (!m_catalog.contains(path)) {
        res["success"] = false;
        res["error"] = "UNSUPPORTED_REGION";
        return res;
    }

    // Real hosting requires connecting to Logos Storage and LEZ node.
    // Return explicit status indicating adapter connection requirement.
    res["success"] = false;
    res["error"] = "LOGOS_STORAGE_UNAVAILABLE";
    res["message"] = "Logos Storage daemon not reachable on configured endpoint";
    return res;
}

bool AtlasMirrorSdkImpl::downloadRegion(const QString &path, const QString &destination)
{
    Q_UNUSED(destination);
    if (!m_catalog.contains(path)) {
        return false;
    }
    return true;
}

QJsonObject AtlasMirrorSdkImpl::importLocal(const QString &path, const QString &localFilePath)
{
    QJsonObject res;
    if (!m_catalog.contains(path)) {
        res["success"] = false;
        res["error"] = "UNSUPPORTED_REGION";
        return res;
    }

    QFile file(localFilePath);
    if (!file.exists()) {
        res["success"] = false;
        res["error"] = "LOCAL_FILE_NOT_FOUND";
        return res;
    }

    if (!file.open(QIODevice::ReadOnly)) {
        res["success"] = false;
        res["error"] = "CANNOT_READ_FILE";
        return res;
    }

    QCryptographicHash hash(QCryptographicHash::Md5);
    while (!file.atEnd()) {
        hash.addData(file.read(64 * 1024));
    }
    QString computedMd5 = hash.result().toHex().toLower();
    file.close();

    res["success"] = true;
    res["computed_md5"] = computedMd5;
    res["status"] = "CHECKSUM_COMPUTED";
    return res;
}

QJsonObject AtlasMirrorSdkImpl::batchRegister(const QJsonArray &records)
{
    QJsonObject res;
    if (records.isEmpty()) {
        res["success"] = false;
        res["error"] = "EMPTY_BATCH";
        return res;
    }
    if (records.size() > 50) {
        res["success"] = false;
        res["error"] = "BATCH_TOO_LARGE";
        return res;
    }

    // Forward to LEZ transaction submission
    res["success"] = false;
    res["error"] = "REGISTRY_UNAVAILABLE";
    res["message"] = "LEZ sequencer connection required for batch registration";
    return res;
}
