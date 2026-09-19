#pragma once

#include <QtCore/QObject>
#include <QtCore/QString>
#include <QtCore/QJsonArray>
#include <QtCore/QJsonObject>

class AppBackend : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString searchFilter READ searchFilter WRITE setSearchFilter NOTIFY searchFilterChanged)
    Q_PROPERTY(QString statusFilter READ statusFilter WRITE setStatusFilter NOTIFY statusFilterChanged)
    Q_PROPERTY(int maxConcurrency READ maxConcurrency WRITE setMaxConcurrency NOTIFY maxConcurrencyChanged)
    Q_PROPERTY(bool telemetryEnabled READ telemetryEnabled WRITE setTelemetryEnabled NOTIFY telemetryEnabledChanged)

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

    Q_INVOKABLE QJsonArray getFilteredRegions();
    Q_INVOKABLE QJsonArray getQueueItems();
    Q_INVOKABLE QJsonArray getDownloadItems();

    Q_INVOKABLE void startHosting(const QString &regionPath);
    Q_INVOKABLE void startBulkHost(const QJsonArray &regionPaths);
    Q_INVOKABLE void cancelHost(const QString &regionPath);
    Q_INVOKABLE void retryHost(const QString &regionPath);
    Q_INVOKABLE void startDownload(const QString &regionPath);

signals:
    void searchFilterChanged();
    void statusFilterChanged();
    void maxConcurrencyChanged();
    void telemetryEnabledChanged();
    void queueUpdated();
    void downloadsUpdated();

private:
    QString m_searchFilter;
    QString m_statusFilter{"ALL"};
    int m_maxConcurrency{2};
    bool m_telemetryEnabled{false};

    QJsonArray m_queue;
    QJsonArray m_downloads;
};
