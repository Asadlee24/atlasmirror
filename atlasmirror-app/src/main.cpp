#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include "backend/app_backend.h"

#include <QFile>

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    app.setApplicationName("AtlasMirror");
    app.setOrganizationName("Logos");

    QQmlApplicationEngine engine;

    AppBackend backend;
    engine.rootContext()->setContextProperty("cBackend", &backend);
    engine.rootContext()->setContextProperty("appBackend", &backend);
    engine.rootContext()->setContextProperty("backend", &backend);

    QUrl url;
    if (QFile::exists(QStringLiteral(":/src/qml/Main.qml"))) {
        url = QUrl(QStringLiteral("qrc:/src/qml/Main.qml"));
    } else {
        url = QUrl::fromLocalFile(QStringLiteral("src/qml/Main.qml"));
    }

    QObject::connect(&engine, &QQmlApplicationEngine::objectCreated,
                     &app, [url](QObject *obj, const QUrl &objUrl) {
        if (!obj && url == objUrl)
            QCoreApplication::exit(-1);
    }, Qt::QueuedConnection);

    engine.load(url);

    return app.exec();
}
