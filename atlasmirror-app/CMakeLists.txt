cmake_minimum_required(VERSION 3.22)
project(atlasmirror_app_backend VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 REQUIRED COMPONENTS Core Quick Qml RemoteObjects)

add_library(atlasmirror_app_backend SHARED
    src/backend/app_backend.cpp
    src/backend/app_backend.h
)

target_include_directories(atlasmirror_app_backend PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/backend
)

target_link_libraries(atlasmirror_app_backend PRIVATE
    Qt6::Core
    Qt6::Quick
    Qt6::Qml
    Qt6::RemoteObjects
)
