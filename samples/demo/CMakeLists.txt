cmake_minimum_required(VERSION 3.20)

project(axio_analyst_demo LANGUAGES CXX)

add_executable(axio_analyst_demo main.cpp)
target_compile_features(axio_analyst_demo PRIVATE cxx_std_17)

if(MSVC)
    target_compile_options(axio_analyst_demo PRIVATE /O2 /W4 /EHsc)
else()
    target_compile_options(axio_analyst_demo PRIVATE -O2 -Wall -Wextra -Wpedantic)
endif()
