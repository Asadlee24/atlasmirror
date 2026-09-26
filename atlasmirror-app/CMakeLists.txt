cmake_minimum_required(VERSION 3.22)
project(atlasmirror_app_backend VERSION 0.1.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Quick Qml RemoteObjects Gui)

add_library(atlasmirror_app_backend SHARED
    src/backend/app_backend.cpp
    src/backend/app_backend.h
    ${CMAKE_CURRENT_SOURCE_DIR}/../atlasmirror-sdk/src/atlasmirror_sdk_impl.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/../atlasmirror-sdk/src/atlasmirror_sdk_impl.h
    qml.qrc
)

target_include_directories(atlasmirror_app_backend PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/backend
    ${CMAKE_CURRENT_SOURCE_DIR}/../atlasmirror-sdk/src
)

target_link_libraries(atlasmirror_app_backend PRIVATE
    Qt6::Core
    Qt6::Quick
    Qt6::Qml
    Qt6::RemoteObjects
)

add_executable(atlasmirror-app
    src/main.cpp
    src/backend/app_backend.cpp
    src/backend/app_backend.h
    ${CMAKE_CURRENT_SOURCE_DIR}/../atlasmirror-sdk/src/atlasmirror_sdk_impl.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/../atlasmirror-sdk/src/atlasmirror_sdk_impl.h
    qml.qrc
)

target_include_directories(atlasmirror-app PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/backend
    ${CMAKE_CURRENT_SOURCE_DIR}/../atlasmirror-sdk/src
)

target_link_libraries(atlasmirror-app PRIVATE
    Qt6::Core
    Qt6::Quick
    Qt6::Qml
    Qt6::Gui
    Qt6::RemoteObjects
)
