cmake_minimum_required(VERSION 3.16)
project(vmf_validator_cpp LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)

enable_testing()

# Place all runtime outputs in a known directory
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_BINARY_DIR}/bin)

# Library
add_library(vmf_validator_cpp SHARED validator.cpp lineage_logger.cpp)
target_compile_definitions(vmf_validator_cpp PRIVATE BUILDING_VMF_VALIDATOR_CPP)
target_include_directories(vmf_validator_cpp PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# Simple test executable (exercises the library)
add_executable(vmf_validator_test validator_test.cpp)
target_link_libraries(vmf_validator_test PRIVATE vmf_validator_cpp)

# Unit tests using Catch2 via FetchContent
include(FetchContent)
FetchContent_Declare(
 catch2
 GIT_REPOSITORY https://github.com/catchorg/Catch2.git
 GIT_TAG v3.4.0
)
FetchContent_MakeAvailable(catch2)

add_executable(unit_tests unit_tests.cpp)
target_link_libraries(unit_tests PRIVATE vmf_validator_cpp Catch2::Catch2WithMain)

# Use Catch2 helper to register tests with CTest (discovers TEST_CASEs)
include(Catch)
catch_discover_tests(unit_tests)

# Register the simple integration test using the target file
add_test(NAME vmf_validator_test COMMAND $<TARGET_FILE:vmf_validator_test>)
set_tests_properties(vmf_validator_test PROPERTIES WORKING_DIRECTORY ${CMAKE_BINARY_DIR})

# Register unit_tests explicitly as well
add_test(NAME unit_tests COMMAND $<TARGET_FILE:unit_tests>)
set_tests_properties(unit_tests PROPERTIES WORKING_DIRECTORY ${CMAKE_BINARY_DIR})

# Add a convenience check target to run ctest
add_custom_target(check
 COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure
 DEPENDS unit_tests vmf_validator_test
)

# Add Python pytest entry if Python3 is available
find_package(Python3 COMPONENTS Interpreter)
if(Python3_Interpreter_FOUND)
 message(STATUS "Python3 found: ${Python3_EXECUTABLE}")
 add_test(NAME pytest COMMAND ${Python3_EXECUTABLE} -m pytest ${CMAKE_SOURCE_DIR}/tests)
 set_tests_properties(pytest PROPERTIES WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
endif()