cmake_minimum_required(VERSION 3.22)
project(consumer_module VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Quick Qml Gui)

set(SDK_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../atlasmirror-sdk/src")

add_library(consumer_module_backend SHARED
    src/consumer_backend.cpp
    src/consumer_backend.h
    ${SDK_SRC_DIR}/atlasmirror_sdk_impl.cpp
    ${SDK_SRC_DIR}/atlasmirror_sdk_impl.h
)

target_include_directories(consumer_module_backend PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${SDK_SRC_DIR}
)

target_link_libraries(consumer_module_backend PRIVATE
    Qt6::Core
    Qt6::Quick
    Qt6::Qml
    Qt6::Gui
)
