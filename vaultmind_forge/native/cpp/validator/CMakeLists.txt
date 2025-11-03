cmake_minimum_required(VERSION 3.16)
project(vmf_validator_cpp LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
add_library(vmf_validator_cpp SHARED validator.cpp)