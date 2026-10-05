.pragma library

var categoryOrder = [
    "system",
    "cpu",
    "memory",
    "gpu",
    "storage",
    "network",
    "display",
    "gaming",
    "power",
    "sensor",
    "peripheral"
]

function categoryRank(category) {
    var index = categoryOrder.indexOf(category)

    if (index < 0)
        return 999

    return index
}

function categoryFor(id, sensor) {
    if (sensor && sensor.category)
        return sensor.category

    var split = id.indexOf(".")

    if (split < 0)
        return "sensor"

    return id.substring(0, split)
}

function merge(systemSensors, sessionSensors) {
    var merged = {}
    var key

    systemSensors = systemSensors || {}
    sessionSensors = sessionSensors || {}

    for (key in systemSensors)
        merged[key] = systemSensors[key]

    for (key in sessionSensors)
        merged[key] = sessionSensors[key]

    return merged
}

function sensorArray(sensors) {
    var result = []

    sensors = sensors || {}

    for (var id in sensors) {
        var sensor = sensors[id] || {}

        result.push({
            id: id,
            name: sensor.name || id,
            category: categoryFor(id, sensor),
            value: sensor.value,
            unit: sensor.unit || "",
            available:
                sensor.available === undefined
                    ? true
                    : Boolean(sensor.available),
            source: sensor.source || "",
            minimum: sensor.minimum,
            maximum: sensor.maximum,
            warning: sensor.warning,
            critical: sensor.critical
        })
    }

    result.sort(function(a, b) {
        var categoryDifference =
            categoryRank(a.category)
            - categoryRank(b.category)

        if (categoryDifference !== 0)
            return categoryDifference

        var nameCompare =
            a.name.localeCompare(b.name)

        if (nameCompare !== 0)
            return nameCompare

        return a.id.localeCompare(b.id)
    })

    return result
}

function bytes(value) {
    var number = Number(value)

    if (!isFinite(number))
        return String(value)

    var units = [
        "B",
        "KiB",
        "MiB",
        "GiB",
        "TiB"
    ]

    var index = 0

    while (
        Math.abs(number) >= 1024
        && index < units.length - 1
    ) {
        number /= 1024
        index++
    }

    var digits = index === 0 ? 0 : 1

    return number.toFixed(digits)
        + " "
        + units[index]
}

function rate(value) {
    return bytes(value) + "/s"
}

function formatValue(sensor, showUnits) {
    if (!sensor)
        return ""

    var value = sensor.value
    var unit = sensor.unit || ""

    if (value === null || value === undefined)
        return "—"

    if (typeof value === "boolean")
        return value ? "Yes" : "No"

    if (unit === "B")
        return bytes(value)

    if (unit === "B/s")
        return rate(value)

    if (
        typeof value === "number"
        && !Number.isInteger(value)
    ) {
        value = Number(value).toFixed(1)
    }

    if (!showUnits || !unit)
        return String(value)

    if (unit === "%")
        return String(value) + "%"

    if (unit === "°C")
        return String(value) + " °C"

    return String(value) + " " + unit
}

function categoryTitle(category) {
    switch (category) {
    case "cpu":
        return "CPU"
    case "gpu":
        return "GPU"
    case "memory":
        return "Memory"
    case "storage":
        return "Storage"
    case "network":
        return "Network"
    case "display":
        return "Display"
    case "gaming":
        return "Gaming"
    case "power":
        return "Power"
    case "system":
        return "System"
    case "sensor":
        return "Sensors"
    case "peripheral":
        return "Peripherals"
    default:
        if (!category)
            return "Other"

        return category.charAt(0).toUpperCase()
            + category.slice(1)
    }
}
