cmake_minimum_required(VERSION 3.22.1)
project("modmenu")

add_library(modmenu SHARED
    jni_bridge.cpp
    memory.cpp
    process.cpp
    aob_scanner.cpp
)

find_library(log-lib log)

target_link_libraries(modmenu
    ${log-lib}
)

target_compile_options(modmenu PRIVATE -O2 -fvisibility=hidden -Wall)
