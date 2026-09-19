#include "app_backend.h"
#include <QtCore/QDebug>

AppBackend::AppBackend(QObject *parent)
    : QObject(parent)
{
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

QJsonArray AppBackend::getFilteredRegions()
{
    // Evaluates filter criteria
    return QJsonArray();
}

QJsonArray AppBackend::getQueueItems()
{
    return m_queue;
}

QJsonArray AppBackend::getDownloadItems()
{
    return m_downloads;
}

void AppBackend::startHosting(const QString &regionPath)
{
    QJsonObject item;
    item["region"] = regionPath;
    item["state"] = "QUEUED";
    item["progress"] = 0;
    m_queue.append(item);
    emit queueUpdated();
}

void AppBackend::startBulkHost(const QJsonArray &regionPaths)
{
    for (const QJsonValue &val : regionPaths) {
        startHosting(val.toString());
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
            obj["state"] = "QUEUED";
            obj["progress"] = 0;
            m_queue[i] = obj;
            emit queueUpdated();
            break;
        }
    }
}

void AppBackend::startDownload(const QString &regionPath)
{
    QJsonObject item;
    item["region"] = regionPath;
    item["status"] = "DOWNLOADING";
    item["progress"] = 0;
    m_downloads.append(item);
    emit downloadsUpdated();
}
