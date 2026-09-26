cmake_minimum_required(VERSION 3.22)
project(atlasmirror_app_backend VERSION 0.1.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Quick Qml Gui)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../atlasmirror-sdk/src/atlasmirror_sdk_impl.cpp")
    set(SDK_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../atlasmirror-sdk/src")
elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../atlasmirror_sdk/src/atlasmirror_sdk_impl.cpp")
    set(SDK_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../atlasmirror_sdk/src")
else()
    set(SDK_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../atlasmirror-sdk/src")
endif()

# Main backend shared library
add_library(atlasmirror_app_backend SHARED
    src/backend/app_backend.cpp
    src/backend/app_backend.h
    ${SDK_SRC_DIR}/atlasmirror_sdk_impl.cpp
    ${SDK_SRC_DIR}/atlasmirror_sdk_impl.h
    qml.qrc
)

target_include_directories(atlasmirror_app_backend PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/backend
    ${SDK_SRC_DIR}
)

target_link_libraries(atlasmirror_app_backend PRIVATE
    Qt6::Core
    Qt6::Quick
    Qt6::Qml
    Qt6::Gui
)

# Canonical Basecamp module plugin shared library
add_library(atlasmirror_app_plugin SHARED
    src/backend/app_backend.cpp
    src/backend/app_backend.h
    ${SDK_SRC_DIR}/atlasmirror_sdk_impl.cpp
    ${SDK_SRC_DIR}/atlasmirror_sdk_impl.h
    qml.qrc
)

target_include_directories(atlasmirror_app_plugin PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/backend
    ${SDK_SRC_DIR}
)

target_link_libraries(atlasmirror_app_plugin PRIVATE
    Qt6::Core
    Qt6::Quick
    Qt6::Qml
    Qt6::Gui
)

# Standalone executable
add_executable(atlasmirror-app
    src/main.cpp
    src/backend/app_backend.cpp
    src/backend/app_backend.h
    ${SDK_SRC_DIR}/atlasmirror_sdk_impl.cpp
    ${SDK_SRC_DIR}/atlasmirror_sdk_impl.h
    qml.qrc
)

target_include_directories(atlasmirror-app PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/backend
    ${SDK_SRC_DIR}
)

target_link_libraries(atlasmirror-app PRIVATE
    Qt6::Core
    Qt6::Quick
    Qt6::Qml
    Qt6::Gui
)
