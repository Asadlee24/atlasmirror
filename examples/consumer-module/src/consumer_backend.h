#pragma once

#include <QtCore/QObject>
#include <QtCore/QString>
#include <QtCore/QJsonObject>
#include <QtCore/QJsonDocument>
#include "atlasmirror_sdk_impl.h"

class ConsumerBackend : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString status READ status NOTIFY statusChanged)
    Q_PROPERTY(QString lastResolvedCid READ lastResolvedCid NOTIFY lastResolvedCidChanged)
    Q_PROPERTY(bool isBusy READ isBusy NOTIFY isBusyChanged)

public:
    explicit ConsumerBackend(QObject *parent = nullptr);
    virtual ~ConsumerBackend() = default;

    QString status() const { return m_status; }
    QString lastResolvedCid() const { return m_lastResolvedCid; }
    bool isBusy() const { return m_isBusy; }

    Q_INVOKABLE QString resolveRegion(const QString &regionPath);
    Q_INVOKABLE bool downloadRegion(const QString &regionPath, const QString &destination);

signals:
    void statusChanged();
    void lastResolvedCidChanged();
    void isBusyChanged();
    void regionResolved(const QString &regionPath, const QString &cid, const QString &checksum);
    void downloadCompleted(const QString &regionPath, bool success, const QString &destPath);

private:
    AtlasmirrorSdkImpl m_sdk;
    QString m_status{"Ready"};
    QString m_lastResolvedCid{""};
    bool m_isBusy{false};
};
