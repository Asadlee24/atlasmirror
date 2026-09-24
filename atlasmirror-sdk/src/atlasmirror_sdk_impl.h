#pragma once

#include <string>
#include <vector>
#include <map>
#include "logos_module_context.h"

/**
 * @brief Public interface of the AtlasMirror Core SDK module.
 * 
 * In the universal authoring model of logos-module-builder, this class
 * exposes the stable API for Basecamp applications and external modules.
 */
class AtlasmirrorSdkImpl : public LogosModuleContext
{
public:
    /**
     * @brief Discovers all regions in the predefined non-overlapping set.
     * @return JSON array string of region objects with path, name, level, parent, and status.
     */
    std::string discoverRegions();

    /**
     * @brief Retrieves detailed metadata for a specific region path.
     * @param path The canonical Geofabrik path (e.g. "asia/pakistan").
     */
    std::string getRegion(const std::string &path);

    /**
     * @brief Resolves metadata for a specific Logos Storage CID.
     * @param cid The content identifier.
     */
    std::string getByCid(const std::string &cid);

    /**
     * @brief Gets child subregions for a decomposed parent country.
     * @param parent The parent identifier (e.g. "us", "india", "china", "russia").
     */
    std::string getChildren(const std::string &parent);

    /**
     * @brief Resolves the download source for a region (Logos Storage CID or Geofabrik fallback).
     * @param path The canonical region path.
     */
    std::string resolveRegion(const std::string &path);

    /**
     * @brief Checks if a newer snapshot is available on Geofabrik for this region.
     * @param path The canonical region path.
     * @return Status JSON string with state: UP_TO_DATE, UPDATE_AVAILABLE, NOT_HOSTED, or ERROR.
     */
    std::string checkUpdate(const std::string &path);

    /**
     * @brief Full hosting workflow: fetch -> verify MD5 -> Logos Storage -> LEZ register.
     * @param path Canonical region path.
     */
    std::string hostRegion(const std::string &path);

    /**
     * @brief Downloads a region snapshot to local destination (from Storage or fallback).
     * @param path Canonical region path.
     * @param destination Absolute local filesystem path.
     */
    bool downloadRegion(const std::string &path, const std::string &destination);

    /**
     * @brief Verifies a local PBF against Geofabrik MD5 and hosts it to Logos Storage & LEZ.
     * @param path Canonical region path.
     * @param localFilePath Absolute path to the local .osm.pbf file.
     */
    std::string importLocal(const std::string &path, const std::string &localFilePath);

    /**
     * @brief Submits a batch registration of multiple region records to LEZ.
     * @param records Array of region record JSON objects as a string.
     */
    std::string batchRegister(const std::string &records);

protected:
    void onContextReady() override;

private:
    void loadPredefinedCatalog();

    struct RegionRecord {
        std::string path;
        std::string name;
        std::string level;
        std::string parent;
        std::string geofabrik_url;
        std::string md5_url;
        bool hosted{false};
        std::string cid;
        std::string checksum;
        std::string version;
    };

    std::map<std::string, RegionRecord> m_catalog;
    std::map<std::string, RegionRecord> m_hostedRecords;
};
