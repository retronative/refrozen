cmake_minimum_required(VERSION 3.25)
project(reFrozen CXX C)

# x86recomp (pinned, with patches/x86recomp applied): scripts/setup_tools.sh.
set(X86RECOMP_DIR "${CMAKE_CURRENT_SOURCE_DIR}/tools/x86recomp" CACHE PATH "")
set(CMAKE_LINK_DEPENDS_NO_SHARED ON)  # no relink when only a runtime library changes
enable_testing()
add_subdirectory("${X86RECOMP_DIR}" x86recomp)

# REFROZEN_DYNAMIC_MODULE (experimental, the first-run builder's proof of
# concept; no release step uses it until first-run setup and packaging
# exist): refrozen is only the launcher and loads the game module, built on
# the player's Mac by scripts/poc/build_module.sh, at run time. Both carry
# REFROZEN_MODULE_STAMP.
option(REFROZEN_DYNAMIC_MODULE "experimental: load the game module at run time" OFF)

if(REFROZEN_DYNAMIC_MODULE)
  execute_process(COMMAND git -C "${CMAKE_CURRENT_SOURCE_DIR}" rev-parse --short=12 HEAD
                  OUTPUT_VARIABLE _rf OUTPUT_STRIP_TRAILING_WHITESPACE)
  execute_process(COMMAND git -C "${X86RECOMP_DIR}" rev-parse --short=12 "HEAD^{tree}"
                  OUTPUT_VARIABLE _x86 OUTPUT_STRIP_TRAILING_WHITESPACE)
  set(REFROZEN_MODULE_STAMP "${_rf}-${_x86}" CACHE STRING "")
  add_executable(refrozen src/main.cpp)
  target_compile_definitions(refrozen PRIVATE REFROZEN_DYNAMIC_MODULE
    REFROZEN_MODULE_STAMP="${REFROZEN_MODULE_STAMP}")
  # The app starts the game by replacing itself with this launcher, so macOS
  # asks the launcher for local network access: give it an Info.plist (its
  # name, a stable identity, the usage description), embedded as
  # __TEXT,__info_plist since the launcher is not a bundle.
  configure_file(src/launcher-Info.plist.in "${CMAKE_CURRENT_BINARY_DIR}/launcher-Info.plist" @ONLY)
  target_link_options(refrozen PRIVATE
    "LINKER:-sectcreate,__TEXT,__info_plist,${CMAKE_CURRENT_BINARY_DIR}/launcher-Info.plist")
  set_property(TARGET refrozen APPEND PROPERTY LINK_DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/launcher-Info.plist")
else()
  # The recompiled modules, generated from the player's own files by scripts/lift.sh
  # (git-ignored). Re-run cmake after lifting.
  set(REFROZEN_GENERATED "${CMAKE_CURRENT_SOURCE_DIR}/game/generated/war3" CACHE PATH "")
  recomp_add_lifted(war3_lifted "${REFROZEN_GENERATED}")
  if(NOT TARGET war3_lifted)
    message(FATAL_ERROR "no lifted code in ${REFROZEN_GENERATED}: run scripts/lift.sh first")
  endif()
  add_executable(refrozen src/main.cpp $<TARGET_OBJECTS:war3_lifted>)
endif()
target_compile_features(refrozen PRIVATE cxx_std_20)
target_include_directories(refrozen PRIVATE "${X86RECOMP_DIR}/src")
# The development default game folder; a dynamic-module launcher (the app's)
# uses the player's data folder instead (src/main.cpp) and names no build path.
if(NOT REFROZEN_DYNAMIC_MODULE)
  target_compile_definitions(refrozen PRIVATE
    REFROZEN_DEFAULT_GAME_DIR="${CMAKE_CURRENT_SOURCE_DIR}/game/native-install")
endif()
# recomp_opengl: game.dll imports opengl32.dll (its OpenGL renderer, "Gfx OpenGL").
target_link_libraries(refrozen PRIVATE recomp_runtime recomp_opengl)
