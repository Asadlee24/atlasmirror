# AtlasMirror SDK Module CMakeLists.txt
# Canonical Logos universal module definition using LogosModule.cmake

cmake_minimum_required(VERSION 3.14)
project(AtlasmirrorSdkPlugin LANGUAGES CXX)

# Include the Logos Module CMake helper
if(DEFINED ENV{LOGOS_MODULE_BUILDER_ROOT})
    include($ENV{LOGOS_MODULE_BUILDER_ROOT}/cmake/LogosModule.cmake)
elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/cmake/LogosModule.cmake")
    include(cmake/LogosModule.cmake)
else()
    find_package(Qt6 REQUIRED COMPONENTS Core Network)
    add_library(atlasmirror_sdk_plugin SHARED
        src/atlasmirror_sdk_impl.h
        src/atlasmirror_sdk_impl.cpp
    )
    target_include_directories(atlasmirror_sdk_plugin PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
    target_link_libraries(atlasmirror_sdk_plugin PRIVATE Qt6::Core Qt6::Network)
    install(TARGETS atlasmirror_sdk_plugin
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin
        ARCHIVE DESTINATION lib
    )
    return()
endif()

# Derive module name from metadata.json
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/metadata.json" METADATA_JSON)
string(JSON MODULE_NAME GET ${METADATA_JSON} name)

# Define the Logos module; glue generation, plugin target, and installation handled automatically
logos_module(
    NAME ${MODULE_NAME}
    SOURCES
        src/atlasmirror_sdk_impl.h
        src/atlasmirror_sdk_impl.cpp
)
