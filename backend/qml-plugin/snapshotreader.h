#pragma once

#include <QObject>
#include <QString>
#include <qqmlintegration.h>

class SnapshotReader : public QObject
{
    Q_OBJECT
    QML_ELEMENT

public:
    explicit SnapshotReader(QObject *parent = nullptr);

    Q_INVOKABLE QString readFile(const QString &path) const;
    Q_INVOKABLE QString runtimeDir() const;
};
