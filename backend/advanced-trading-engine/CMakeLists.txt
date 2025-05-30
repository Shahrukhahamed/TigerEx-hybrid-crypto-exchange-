cmake_minimum_required(VERSION 3.16)
project(TigerExAdvancedTradingEngine)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Compiler flags for optimization
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -march=native -mtune=native")
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -DDEBUG")

# Find required packages
find_package(Boost REQUIRED COMPONENTS system filesystem thread json)
find_package(PkgConfig REQUIRED)
find_package(Threads REQUIRED)

# Find Redis++
pkg_check_modules(REDIS++ REQUIRED redis++)

# Find PostgreSQL
find_package(PostgreSQL REQUIRED)

# Find Kafka
find_path(KAFKA_INCLUDE_DIR kafka/KafkaProducer.h)
find_library(KAFKA_LIBRARY NAMES rdkafka++)

# Find Prometheus
find_path(PROMETHEUS_INCLUDE_DIR prometheus/counter.h)
find_library(PROMETHEUS_LIBRARY NAMES prometheus-cpp-core)

# Include directories
include_directories(${CMAKE_SOURCE_DIR}/include)
include_directories(${Boost_INCLUDE_DIRS})
include_directories(${PostgreSQL_INCLUDE_DIRS})
include_directories(${REDIS++_INCLUDE_DIRS})
include_directories(${KAFKA_INCLUDE_DIR})
include_directories(${PROMETHEUS_INCLUDE_DIR})

# Source files
set(SOURCES
    src/main.cpp
)

# Create executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Link libraries
target_link_libraries(${PROJECT_NAME}
    ${Boost_LIBRARIES}
    ${PostgreSQL_LIBRARIES}
    ${REDIS++_LIBRARIES}
    ${KAFKA_LIBRARY}
    ${PROMETHEUS_LIBRARY}
    Threads::Threads
    pqxx
)

# Compiler-specific options
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra -Wpedantic)
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Installation
install(TARGETS ${PROJECT_NAME} DESTINATION bin)

# Testing
enable_testing()
add_subdirectory(tests)