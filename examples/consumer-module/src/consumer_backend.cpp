#include "consumer_backend.h"
#include <QtCore/QThreadPool>
#include <QtCore/QMetaObject>

ConsumerBackend::ConsumerBackend(QObject *parent)
    : QObject(parent)
{
}

QString ConsumerBackend::resolveRegion(const QString &regionPath)
{
    m_isBusy = true;
    emit isBusyChanged();

    std::string resStr = m_sdk.resolveRegion(regionPath.toStdString());
    QJsonDocument doc = QJsonDocument::fromJson(QByteArray::fromStdString(resStr));
    QJsonObject obj = doc.object();

    if (obj.value("found").toBool() || !obj.value("cid").toString().isEmpty()) {
        m_lastResolvedCid = obj.value("cid").toString();
        m_status = QString("Resolved %1 -> %2").arg(regionPath, m_lastResolvedCid);
        emit regionResolved(regionPath, m_lastResolvedCid, obj.value("checksum").toString());
    } else {
        m_status = QString("Region not found in registry: %1").arg(regionPath);
    }

    m_isBusy = false;
    emit statusChanged();
    emit lastResolvedCidChanged();
    emit isBusyChanged();

    return QString::fromStdString(resStr);
}

bool ConsumerBackend::downloadRegion(const QString &regionPath, const QString &destination)
{
    m_isBusy = true;
    m_status = QString("Downloading %1 to %2...").arg(regionPath, destination);
    emit isBusyChanged();
    emit statusChanged();

    QThreadPool::globalInstance()->start([this, regionPath, destination]() {
        bool ok = m_sdk.downloadRegion(regionPath.toStdString(), destination.toStdString());
        QMetaObject::invokeMethod(this, [this, regionPath, destination, ok]() {
            m_isBusy = false;
            m_status = ok ? QString("Download complete: %1").arg(destination)
                          : QString("Download failed: %1").arg(regionPath);
            emit isBusyChanged();
            emit statusChanged();
            emit downloadCompleted(regionPath, ok, destination);
        }, Qt::QueuedConnection);
    });

    return true;
}
