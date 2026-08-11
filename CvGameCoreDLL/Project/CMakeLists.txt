#########################################################################
# CvGameCoreDLL - CMakeLists.txt
#########################################################################

cmake_minimum_required(VERSION 3.20)

#### Tools (TOOLKIT / PSDK) ####
# Equivalent to the original CC/CPP/LD/RC lines, which pointed straight at
# cl.exe/link.exe/rc.exe under a specific MSVC toolkit + Platform SDK:
#   CC="$(TOOLKIT)\bin\cl.exe"      TOOLKIT = ...\VC\Tools\MSVC\<ver>\bin\Hostx64\x64
#   LD="$(TOOLKIT)\bin\link.exe"
#   RC="$(PSDK)\bin\rc.exe"         PSDK    = ...\Windows Kits\<ver> (or the old v7.0A SDK)
#
# These must be set (via -D on the command line, or edited below) *before*
# project() runs, since that's when CMake locates the compiler/linker/RC
# compiler. If left empty, CMake falls back to auto-detecting the toolset
# from your environment (e.g. a "Developer Command Prompt for VS" or -T/-A),
# same as leaving TOOLKIT/PSDK commented out in the original Makefile.
set(TOOLKIT "C:/Program Files (x86)/Civ4SDK/Microsoft Visual C++ Toolkit 2003" CACHE
        PATH "Path to VC\\Tools\\MSVC\\<ver>\\bin\\Hostx64\\x64 (folder containing cl.exe/link.exe)")
set(PSDK    "C:/Program Files (x86)/Civ4SDK/WindowsSDK" CACHE
        PATH "Path to the Windows/Platform SDK root (folder containing bin\\rc.exe, Include\\, Lib\\)")


set(CMAKE_CXX_COMPILER "${TOOLKIT}/bin/cl.exe" CACHE FILEPATH "" FORCE)
set(CMAKE_C_COMPILER   "${TOOLKIT}/bin/cl.exe" CACHE FILEPATH "" FORCE)
set(CMAKE_LINKER       "${TOOLKIT}/bin/link.exe" CACHE FILEPATH "" FORCE)
set(CMAKE_RC_COMPILER "${PSDK}/bin/rc.exe" CACHE FILEPATH "" FORCE)
set(CMAKE_NINJA_CMCLDEPS_RC OFF)


project(CvGameCoreDLL CXX RC)

if(NOT MSVC)
    message(FATAL_ERROR "This project only supports the MSVC toolchain (matches the original NMAKE build).")
endif()

#### Multi-config setup: replace the default VS configs with the Civ4 ones ####
set(CMAKE_CONFIGURATION_TYPES "Debug;Debug_opt;Release;Profile;Final_Release"
    CACHE STRING "Available build configurations" FORCE)

#### User setup (equivalent to Makefile.user / Makefile.project) ####
# Point these at your toolkit/SDK/mod folder just like the old TOOLKIT/PSDK/
# YOURMOD variables. They can also be set on the cmake command line with -D.
set(CIV4_LIB_INSTALL_PATH "D:/Civ4/Beyond the Sword/Mods/AdvCiv/CvGameCoreDLL" CACHE PATH "Path to the directory where boost and python are stored")
set(YOURMOD  "D:/Civ4/Beyond the Sword/Mods/AdvCiv/" CACHE PATH "Mod Assets dir to auto-copy the built DLL/PDB into")
set(YOURMOD2 "" CACHE PATH "Second mod Assets dir to auto-copy the built DLL into")
set(YOURLOGS "" CACHE PATH "Directory whose *.log files get deleted after a build")
set(SOURCE_DIR "${CMAKE_SOURCE_DIR}/../" CACHE PATH "Root directory containing the DLL's .cpp sources")
set(CUSTOM_CFLAGS  "" CACHE STRING "Extra compiler flags (like Makefile.user's CUSTOM_CFLAGS)")
set(CUSTOM_LDFLAGS "" CACHE STRING "Extra linker flags (like Makefile.user's CUSTOM_LDFLAGS)")
set(BLACKLIST "" CACHE STRING "Optional source file to blacklist (e.g. CvTextScreens), stubbed out instead of compiled")

# Environment variable overrides, mirroring the original makefile's behaviour
if(DEFINED ENV{CIV4_LIB_INSTALL_PATH} AND CIV4_LIB_INSTALL_PATH STREQUAL "")
    set(CIV4_LIB_INSTALL_PATH "$ENV{CIV4_LIB_INSTALL_PATH}")
endif()

set(BOOST_LIB_PATH "${SOURCE_DIR}/Boost-1.32.0")


#### Sources ####
# The original makefile builds its source list from up to 15 subdirectories
# (SUBDIR1..SUBDIR15) plus SOURCE_DIR itself. Glob everything recursively
# instead; exclude the precompile stub, which is built separately below.
file(GLOB CVGAMECORE_SOURCES CONFIGURE_DEPENDS "${SOURCE_DIR}/*.cpp")
list(FILTER CVGAMECORE_SOURCES EXCLUDE REGEX ".*/_precompile\\.cpp$")

message(STATUS "SOURCE: ${CVGAMECORE_SOURCES}")

if(BLACKLIST)
    list(FILTER CVGAMECORE_SOURCES EXCLUDE REGEX ".*/${BLACKLIST}\\.cpp$")
endif()

set(CVGAMECORE_PRECOMPILE_SOURCE "${SOURCE_DIR}/_precompile.cpp")

add_library(CvGameCoreDLL SHARED ${CVGAMECORE_SOURCES})

if(EXISTS "${SOURCE_DIR}/CvGameCoreDLL.rc")
    target_sources(CvGameCoreDLL PRIVATE "${CMAKE_SOURCE_DIR}/CvGameCoreDLL.rc")
    # Original only wires the .rc into the Final_Release link; RC compiles
    # cheaply for the others too, so it's left enabled for all configs here.
endif()

if(BLACKLIST)
    # Replaces the blacklisted source with an empty translation unit,
    # like the makefile's dummy-cpp rule.
    set(_dummy "${CMAKE_BINARY_DIR}/${BLACKLIST}-dummy.cpp")
    file(WRITE "${_dummy}" "// blacklisted: ${BLACKLIST}\n")
    target_sources(CvGameCoreDLL PRIVATE "${_dummy}")
endif()




set_target_properties(CvGameCoreDLL PROPERTIES
    OUTPUT_NAME "CvGameCoreDLL"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/$<CONFIG>"
    PDB_NAME "CvGameCoreDLL"
    PDB_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/$<CONFIG>"
)

#### Precompiled header (CvGameCoreDLL.h via _precompile.cpp) ####
if(EXISTS "${CVGAMECORE_PRECOMPILE_SOURCE}")
    set(TARGET_PCH CvGameCoreDLL.pch)
    add_library(${TARGET_PCH} OBJECT ${CVGAMECORE_PRECOMPILE_SOURCE})
    target_compile_options(${TARGET_PCH} PRIVATE
            /YcCvGameCoreDLL.h
            /D_USRDLL
            /Fp${TARGET_PCH}
    )
    set_target_properties(${TARGET_PCH} PROPERTIES
            COMPILE_PDB_NAME ${TARGET_PCH}
            COMPILE_PDB_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
    )
    target_include_directories(${TARGET_PCH} PRIVATE
            "${TOOLKIT}/include"
            "${PSDK}/include"
            "${SOURCE_DIR}/Boost-1.32.0/include"
            "${SOURCE_DIR}/Python24/include"
            "C:/Program Files (x86)/Microsoft Visual Studio 10.0/VC/include"
    )
    target_precompile_headers(CvGameCoreDLL PRIVATE "${SOURCE_DIR}/CvGameCoreDLL.h")
endif()

#### Includes (GLOBAL_INCS + PROJECT_INCS) ####
target_include_directories(CvGameCoreDLL PRIVATE
    "${SOURCE_DIR}/Boost-1.32.0/include"
    "${SOURCE_DIR}/Python24/include"
    "${TOOLKIT}/include"
    "${PSDK}/Include"
    "${PSDK}/Include/mfc"
    "C:/Program Files (x86)/Microsoft Visual Studio 10.0/VC/include"
)


#### Libraries (GLOBAL_LIBS + PROJECT_LIBS) ####
target_link_directories(CvGameCoreDLL PRIVATE
    "${SOURCE_DIR}/Python24/libs"
    "${SOURCE_DIR}/Boost-1.32.0/libs/"
    "${TOOLKIT}/lib/"
        "${PSDK}/lib"
)


target_link_libraries(CvGameCoreDLL PRIVATE
    boost_python-vc71-mt-1_32.lib
    winmm.lib
    user32.lib
    msvcprt.lib
)

#### Global compile flags (GLOBAL_CFLAGS) ####
target_compile_options(CvGameCoreDLL PRIVATE
    /D_USRDLL /GR /Gy /EHsc /Gd /Gm- /WX /W4
    ${CUSTOM_CFLAGS}
)

#### Per-configuration defines and flags ####
target_compile_definitions(CvGameCoreDLL PRIVATE
    $<$<CONFIG:Debug>:_DEBUG>
    $<$<CONFIG:Debug_opt>:NDEBUG>
    $<$<CONFIG:Release>:NDEBUG>
    $<$<CONFIG:Profile>:NDEBUG>
    $<$<CONFIG:Final_Release>:NDEBUG>
)

set_target_properties(CvGameCoreDLL PROPERTIES
        MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:DLL>")

set(CMAKE_CXX_FLAGS_DEBUG "/nologo /Od /RTC1 /DWIN32 /D_WINDOWS /D_USRDLL /D_DEBUG /MD /GR /Gy /EHsc /Gd /Gm-")

target_compile_options(CvGameCoreDLL PRIVATE
    # Debug_opt: an almost-Release build, still with debug info
    $<$<CONFIG:Debug_opt>:/O2 /G7 /arch:SSE2 /Z7>
    # Release: optimized, no debug info
    $<$<CONFIG:Release>:/O2 /G7 /arch:SSE2>
    # Profile: like Release but with /Z7 for symbols
    $<$<CONFIG:Profile>:/O2 /G7 /arch:SSE2 /Z7>
    # Final_Release: Release plus whole-program optimization
    $<$<CONFIG:Final_Release>:/O2 /G7 /arch:SSE2 /GL>
)

#set(CMAKE_SHARED_LINKER_FLAGS_DEBUG "/debug /INCREMENTAL:YES")
#### Link flags ####
target_link_options(CvGameCoreDLL PRIVATE
    /NOLOGO /SUBSYSTEM:WINDOWS /LARGEADDRESSAWARE /TLBID:1
    ${CUSTOM_LDFLAGS}
    $<$<CONFIG:Debug>:/INCREMENTAL /DEBUG>
    $<$<CONFIG:Debug_opt>:/INCREMENTAL /DEBUG>
    $<$<CONFIG:Release>:/INCREMENTAL:NO /OPT:REF /OPT:ICF>
    $<$<CONFIG:Profile>:/INCREMENTAL /DEBUG>
    $<$<CONFIG:Final_Release>:/LTCG /INCREMENTAL:NO /OPT:REF /OPT:ICF>
)



#### Post-build steps (equivalent to the "build:" target) ####
if(YOURMOD)
    add_custom_command(TARGET CvGameCoreDLL POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory "${YOURMOD}/Assets"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "$<TARGET_FILE:CvGameCoreDLL>" "${YOURMOD}/Assets/"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "$<TARGET_PDB_FILE:CvGameCoreDLL>" "${YOURMOD}/Assets/"
        COMMENT "Copying CvGameCoreDLL.dll/.pdb to ${YOURMOD} Assets"
    )
endif()

if(YOURMOD2)
    add_custom_command(TARGET CvGameCoreDLL POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory "${YOURMOD2}/Assets"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "$<TARGET_FILE:CvGameCoreDLL>" "${YOURMOD2}/Assets/"
        COMMENT "Copying CvGameCoreDLL.dll to YOURMOD2 Assets"
    )
endif()

if(YOURLOGS)
    add_custom_command(TARGET CvGameCoreDLL POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E rm -f "${YOURLOGS}/*.log"
        COMMENT "Deleting old logs in YOURLOGS"
    )
endif()

#### Notes on things NOT carried over from the Makefile ####
# - fastdep-based dependency-file generation: unnecessary: CMake/MSBuild's
#   own incremental build + CONFIGURE_DEPENDS globbing replace it.
# - The "Assert" configuration was already removed upstream; not re-added
#   here. Add a config block above if you need it back.
