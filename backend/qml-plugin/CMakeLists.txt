cmake_minimum_required(VERSION 3.21)

project(
    SystemStatusQml
    VERSION 1.0.0
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

set(
    QT_QML_OUTPUT_DIRECTORY
    "${CMAKE_BINARY_DIR}/qml"
)

find_package(
    Qt6 REQUIRED
    COMPONENTS
        Core
        Qml
)

qt_standard_project_setup(REQUIRES 6.8)

qt_add_qml_module(
    systemstatus
    URI org.systemstatus.private.status
    VERSION 1.0
    SOURCES
        snapshotreader.cpp
        snapshotreader.h
)

target_link_libraries(
    systemstatus
    PRIVATE
        Qt6::Core
        Qt6::Qml
)

#
# Keep the private System Status QML module self-contained.
#
# The Qt-generated plugin links against libsystemstatus.so.
# At runtime both libraries live in the same QML module
# directory, so resolve the companion library via $ORIGIN.
#
set_target_properties(
    systemstatusplugin
    PROPERTIES
        BUILD_WITH_INSTALL_RPATH TRUE
        INSTALL_RPATH "$ORIGIN"
)

#
# Mirror the production layout in the build tree so local
# QML smoke tests exercise the same library relationship.
#
add_custom_command(
    TARGET systemstatusplugin
    POST_BUILD

    COMMAND
        ${CMAKE_COMMAND}
        -E copy_if_different
        $<TARGET_FILE:systemstatus>
        $<TARGET_FILE_DIR:systemstatusplugin>/

    VERBATIM
)
