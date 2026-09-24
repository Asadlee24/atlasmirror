cmake_minimum_required(VERSION 3.22)
project(atlasmirror_sdk VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 REQUIRED COMPONENTS Core Network)

add_library(atlasmirror_sdk SHARED
    src/atlasmirror_sdk_impl.cpp
    src/atlasmirror_sdk_impl.h
)
set_target_properties(atlasmirror_sdk PROPERTIES OUTPUT_NAME "atlasmirror_sdk_plugin")

add_library(atlasmirror_sdk_plugin SHARED
    src/atlasmirror_sdk_impl.cpp
    src/atlasmirror_sdk_impl.h
)

target_include_directories(atlasmirror_sdk PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)
target_include_directories(atlasmirror_sdk_plugin PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(atlasmirror_sdk PRIVATE
    Qt6::Core
    Qt6::Network
)
target_link_libraries(atlasmirror_sdk_plugin PRIVATE
    Qt6::Core
    Qt6::Network
)

install(TARGETS atlasmirror_sdk atlasmirror_sdk_plugin
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
    ARCHIVE DESTINATION lib
)
