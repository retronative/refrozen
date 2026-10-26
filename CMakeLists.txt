cmake_minimum_required(VERSION 3.25)
project(reFrozen CXX C)

# x86recomp (pinned, with patches/x86recomp applied): scripts/setup_tools.sh.
set(X86RECOMP_DIR "${CMAKE_CURRENT_SOURCE_DIR}/tools/x86recomp" CACHE PATH "")
set(CMAKE_LINK_DEPENDS_NO_SHARED ON)  # no relink when only a runtime library changes
enable_testing()
add_subdirectory("${X86RECOMP_DIR}" x86recomp)

# REFROZEN_DYNAMIC_MODULE (first-run builder proof of concept): refrozen is
# only the launcher and loads the game module, built on the player's Mac by
# scripts/poc/build_module.sh, at run time. Both carry REFROZEN_MODULE_STAMP.
option(REFROZEN_DYNAMIC_MODULE "load the game module at run time" OFF)

if(REFROZEN_DYNAMIC_MODULE)
  execute_process(COMMAND git -C "${CMAKE_CURRENT_SOURCE_DIR}" rev-parse --short=12 HEAD
                  OUTPUT_VARIABLE _rf OUTPUT_STRIP_TRAILING_WHITESPACE)
  execute_process(COMMAND git -C "${X86RECOMP_DIR}" rev-parse --short=12 "HEAD^{tree}"
                  OUTPUT_VARIABLE _x86 OUTPUT_STRIP_TRAILING_WHITESPACE)
  set(REFROZEN_MODULE_STAMP "${_rf}-${_x86}" CACHE STRING "")
  add_executable(refrozen src/main.cpp)
  target_compile_definitions(refrozen PRIVATE REFROZEN_DYNAMIC_MODULE
    REFROZEN_MODULE_STAMP="${REFROZEN_MODULE_STAMP}")
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
target_compile_definitions(refrozen PRIVATE
  REFROZEN_DEFAULT_GAME_DIR="${CMAKE_CURRENT_SOURCE_DIR}/game/native-install")
# recomp_opengl: game.dll imports opengl32.dll (its OpenGL renderer, "Gfx OpenGL").
target_link_libraries(refrozen PRIVATE recomp_runtime recomp_opengl)
