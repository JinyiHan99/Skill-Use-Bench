cmake_minimum_required(VERSION 3.20)
project(cache_service LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)
set(GTEST_VERSION v1.17.0)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/${GTEST_VERSION}.zip
)
FetchContent_MakeAvailable(googletest)

add_library(cache_service
  src/cache.cpp
)
target_include_directories(cache_service PUBLIC include)

add_executable(cache_tests
  tests/cache_test.cpp
)
target_link_libraries(cache_tests cache_service GTest::gtest GTest::gtest_main)

enable_testing()
add_test(NAME CacheTests COMMAND cache_tests)
