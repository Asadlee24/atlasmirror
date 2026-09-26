#pragma once

#include <QtCore/QObject>
#include <QtCore/QString>
#include <QtCore/QJsonArray>
#include <QtCore/QJsonObject>
#include <QtCore/QVariantList>
#include <QtCore/QSet>
#include <QtCore/QMutex>
#include <QtCore/QThreadPool>
#include "atlasmirror_sdk_impl.h"

class AppBackend : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString searchFilter READ searchFilter WRITE setSearchFilter NOTIFY searchFilterChanged)
    Q_PROPERTY(QString statusFilter READ statusFilter WRITE setStatusFilter NOTIFY statusFilterChanged)
    Q_PROPERTY(int maxConcurrency READ maxConcurrency WRITE setMaxConcurrency NOTIFY maxConcurrencyChanged)
    Q_PROPERTY(bool telemetryEnabled READ telemetryEnabled WRITE setTelemetryEnabled NOTIFY telemetryEnabledChanged)
    Q_PROPERTY(QJsonArray regions READ regions NOTIFY regionsUpdated)
    Q_PROPERTY(QJsonArray queue READ queue NOTIFY queueUpdated)
    Q_PROPERTY(QJsonArray downloads READ downloads NOTIFY downloadsUpdated)
    Q_PROPERTY(QJsonObject lastOperationResult READ lastOperationResult NOTIFY operationResultChanged)

public:
    explicit AppBackend(QObject *parent = nullptr);
    virtual ~AppBackend() = default;

    QString searchFilter() const { return m_searchFilter; }
    void setSearchFilter(const QString &filter);

    QString statusFilter() const { return m_statusFilter; }
    void setStatusFilter(const QString &filter);

    int maxConcurrency() const { return m_maxConcurrency; }
    void setMaxConcurrency(int val);

    bool telemetryEnabled() const { return m_telemetryEnabled; }
    void setTelemetryEnabled(bool val);

    QJsonArray regions() const;
    QJsonArray queue() const;
    QJsonArray downloads() const;
    QJsonObject lastOperationResult() const;

    Q_INVOKABLE QJsonArray getFilteredRegions();
    Q_INVOKABLE QJsonArray getQueueItems();
    Q_INVOKABLE QJsonArray getDownloadItems();

    // Direct Asynchronous Operations backed by AtlasmirrorSdkImpl (zero CLI subprocess dependencies)
    Q_INVOKABLE void refreshIndex();
    Q_INVOKABLE void hostRegion(const QString &regionPath);
    Q_INVOKABLE void startBulkHost(const QJsonArray &regionPaths);
    Q_INVOKABLE void cancelHost(const QString &regionPath);
    Q_INVOKABLE void retryHost(const QString &regionPath);
    Q_INVOKABLE void clearCompletedQueue();
    Q_INVOKABLE void retryAllFailed();

    Q_INVOKABLE void startDownload(const QString &regionPath);
    Q_INVOKABLE void copyToClipboard(const QString &text);
    Q_INVOKABLE QString queryRegistry(const QString &queryType, const QString &queryValue);
    Q_INVOKABLE QString importLocal(const QString &regionPath, const QString &localFilePath);
    Q_INVOKABLE QString updateCheck(const QString &regionPath);

signals:
    void searchFilterChanged();
    void statusFilterChanged();
    void maxConcurrencyChanged();
    void telemetryEnabledChanged();
    void regionsUpdated();
    void queueUpdated();
    void downloadsUpdated();
    void operationResultChanged();

private:
    void loadPredefinedCatalog();
    bool isCancelled(const QString &regionPath);

    QString m_searchFilter;
    QString m_statusFilter{"ALL"};
    int m_maxConcurrency{2};
    bool m_telemetryEnabled{false};

    mutable QMutex m_mutex;
    QJsonArray m_regions;
    QJsonArray m_queue;
    QJsonArray m_downloads;
    QJsonObject m_lastResult;

    QSet<QString> m_cancelledRegions;

    AtlasmirrorSdkImpl m_sdk;
};
