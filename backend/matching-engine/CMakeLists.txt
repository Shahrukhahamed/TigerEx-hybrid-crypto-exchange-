cmake_minimum_required(VERSION 3.16)
project(TigerExMatchingEngine)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)

# Add include directories
include_directories(include)
include_directories(/usr/local/include)

# Add executable
add_executable(matching_engine src/main.cpp)

# Link libraries
target_link_libraries(matching_engine 
    Threads::Threads
    pthread
)

# Compiler flags for optimization
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -march=native")
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -DDEBUG")

# Install nlohmann/json and websocketpp headers
include(FetchContent)

FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
)

FetchContent_Declare(
    websocketpp
    GIT_REPOSITORY https://github.com/zaphoyd/websocketpp.git
    GIT_TAG 0.8.2
)

FetchContent_MakeAvailable(nlohmann_json websocketpp)

target_link_libraries(matching_engine nlohmann_json::nlohmann_json)
target_include_directories(matching_engine PRIVATE ${websocketpp_SOURCE_DIR})

# Enable testing
enable_testing()
add_subdirectory(tests)