#include "snapshotreader.h"

#include <QFile>
#include <QIODevice>

SnapshotReader::SnapshotReader(QObject *parent)
    : QObject(parent)
{
}

QString SnapshotReader::readFile(const QString &path) const
{
    QFile file(path);

    if (!file.open(QIODevice::ReadOnly | QIODevice::Text))
        return QString();

    return QString::fromUtf8(file.readAll());
}

QString SnapshotReader::runtimeDir() const
{
    return qEnvironmentVariable("XDG_RUNTIME_DIR");
}
