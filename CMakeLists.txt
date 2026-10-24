cmake_minimum_required(VERSION 3.25)
project(reFrozen CXX C)

# x86recomp (pinned, with patches/x86recomp applied): scripts/setup_tools.sh.
set(X86RECOMP_DIR "${CMAKE_CURRENT_SOURCE_DIR}/tools/x86recomp" CACHE PATH "")
set(CMAKE_LINK_DEPENDS_NO_SHARED ON)  # no relink when only a runtime library changes
enable_testing()
add_subdirectory("${X86RECOMP_DIR}" x86recomp)

# The recompiled modules, generated from the player's own files by scripts/lift.sh
# (git-ignored). Re-run cmake after lifting.
set(REFROZEN_GENERATED "${CMAKE_CURRENT_SOURCE_DIR}/game/generated/war3" CACHE PATH "")
recomp_add_lifted(war3_lifted "${REFROZEN_GENERATED}")
if(NOT TARGET war3_lifted)
  message(FATAL_ERROR "no lifted code in ${REFROZEN_GENERATED}: run scripts/lift.sh first")
endif()

add_executable(refrozen src/main.cpp $<TARGET_OBJECTS:war3_lifted>)
target_compile_features(refrozen PRIVATE cxx_std_20)
target_include_directories(refrozen PRIVATE "${X86RECOMP_DIR}/src")
target_compile_definitions(refrozen PRIVATE
  REFROZEN_DEFAULT_GAME_DIR="${CMAKE_CURRENT_SOURCE_DIR}/game/native-install")
target_link_libraries(refrozen PRIVATE recomp_runtime)
