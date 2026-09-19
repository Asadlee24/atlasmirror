#pragma once

#include <QtCore/QObject>
#include <QtCore/QString>
#include <QtCore/QJsonArray>
#include <QtCore/QJsonObject>
#include <QtCore/QMap>

/**
 * @brief Public interface of the AtlasMirror Core SDK module.
 * 
 * In the universal authoring model of logos-module-builder, this class
 * exposes the stable API for Basecamp applications and external modules.
 */
class AtlasMirrorSdkImpl : public QObject
{
    Q_OBJECT

public:
    explicit AtlasMirrorSdkImpl(QObject *parent = nullptr);
    virtual ~AtlasMirrorSdkImpl() = default;

    /**
     * @brief Discovers all regions in the predefined non-overlapping set.
     * @return Array of region objects with path, name, level, parent, and status.
     */
    Q_INVOKABLE QJsonArray discoverRegions();

    /**
     * @brief Retrieves detailed metadata for a specific region path.
     * @param path The canonical Geofabrik path (e.g. "asia/pakistan").
     */
    Q_INVOKABLE QJsonObject getRegion(const QString &path);

    /**
     * @brief Resolves metadata for a specific Logos Storage CID.
     * @param cid The content identifier.
     */
    Q_INVOKABLE QJsonObject getByCid(const QString &cid);

    /**
     * @brief Gets child subregions for a decomposed parent country.
     * @param parent The parent identifier (e.g. "us", "india", "china", "russia").
     */
    Q_INVOKABLE QJsonArray getChildren(const QString &parent);

    /**
     * @brief Resolves the download source for a region (Logos Storage CID or Geofabrik fallback).
     * @param path The canonical region path.
     */
    Q_INVOKABLE QJsonObject resolveRegion(const QString &path);

    /**
     * @brief Checks if a newer snapshot is available on Geofabrik for this region.
     * @param path The canonical region path.
     * @return Status object with state: UP_TO_DATE, UPDATE_AVAILABLE, NOT_HOSTED, or ERROR.
     */
    Q_INVOKABLE QJsonObject checkUpdate(const QString &path);

    /**
     * @brief Full hosting workflow: fetch -> verify MD5 -> Logos Storage -> LEZ register.
     * @param path Canonical region path.
     */
    Q_INVOKABLE QJsonObject hostRegion(const QString &path);

    /**
     * @brief Downloads a region snapshot to local destination (from Storage or fallback).
     * @param path Canonical region path.
     * @param destination Absolute local filesystem path.
     */
    Q_INVOKABLE bool downloadRegion(const QString &path, const QString &destination);

    /**
     * @brief Verifies a local PBF against Geofabrik MD5 and hosts it to Logos Storage & LEZ.
     * @param path Canonical region path.
     * @param localFilePath Absolute path to the local .osm.pbf file.
     */
    Q_INVOKABLE QJsonObject importLocal(const QString &path, const QString &localFilePath);

    /**
     * @brief Submits a batch registration of multiple region records to LEZ.
     * @param records Array of region record JSON objects.
     */
    Q_INVOKABLE QJsonObject batchRegister(const QJsonArray &records);

private:
    void loadPredefinedCatalog();
    QMap<QString, QJsonObject> m_catalog;
    QMap<QString, QJsonObject> m_hostedRecords;
};
