cmake_minimum_required(VERSION 3.20)
project(json_parser LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(json_parser
  src/json_parser.cpp
)
target_include_directories(json_parser PUBLIC include)

# Tests not yet configured
