// reFrozen: Warcraft III: The Frozen Throne 1.26a, recompiled.
//
//   refrozen [--game <install dir>] [game arguments...]
//
// The install dir is the player's own 1.26a install (scripts/native_install.py);
// it defaults to REFROZEN_GAME_DIR, then to the repository's game/native-install.
// war3.exe is the process image; the DLLs it and game.dll use are lifted with
// it and listed below in load-dependency order (an importer after what it
// imports), which is also the order they are mapped in.

#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <string>

#include "runtime/runtime.h"

namespace {

constexpr const char* kGuestDir = "C:\\Program Files\\Warcraft III";
constexpr const char* kWar3Key = "Software\\Blizzard Entertainment\\Warcraft III";

recomp::GameConfig Config() {
  recomp::GameConfig g;
  g.id = "refrozen";
  g.guest_dir = kGuestDir;
  g.exe_name = "war3.exe";
  // What the RoC and TFT installers write (InstallerFileList.xml <registry_key>,
  // values observed in the official install under Wine).
  const std::string dir = std::string(kGuestDir) + "\\";
  for (const char* root : {"HKLM\\", "HKCU\\"}) {
    g.registry.push_back({std::string(root) + kWar3Key, "InstallPath", dir});
    g.registry.push_back({std::string(root) + kWar3Key, "GamePath", dir + "Frozen Throne.exe"});
  }
  g.registry.push_back({std::string("HKCU\\") + kWar3Key, "Program", dir + "Warcraft III.exe"});
  g.lifted_dlls = {
      {"msvcr80.dll"},  // imported by war3.exe, game.dll, Storm.dll
      {"Storm.dll"},    // imported by war3.exe and game.dll (by ordinal)
      {"Mss32.dll"},    // imported by war3.exe and game.dll
      {"game.dll"},     // LoadLibrary'd by war3.exe
      {"redist\\miles\\Mp3dec.asi"},  // Miles providers, LoadLibrary'd by Mss32
      {"redist\\miles\\Mssfast.m3d"},
      {"redist\\miles\\Msseax2.m3d"},
      {"redist\\miles\\Mssdolby.m3d"},
      {"redist\\miles\\Reverb3.flt"},
  };
  return g;
}

}  // namespace

int main(int argc, char** argv) {
  const char* env = std::getenv("REFROZEN_GAME_DIR");
  std::string game_dir = env ? env : REFROZEN_DEFAULT_GAME_DIR;
  std::string args;
  for (int i = 1; i < argc; i++) {
    std::string a = argv[i];
    if (a == "--game" && i + 1 < argc) {
      game_dir = argv[++i];
      continue;
    }
    args += (args.empty() ? "" : " ") + a;
  }
  const std::filesystem::path exe = std::filesystem::path(game_dir) / "war3.exe";
  if (!std::filesystem::is_regular_file(exe)) {
    std::fprintf(stderr, "refrozen: %s not found (install with scripts/native_install.py, "
                         "or pass --game <install dir>)\n", exe.c_str());
    return 2;
  }
  return recomp::RunProcess(Config(), exe.string(), game_dir, args);
}
