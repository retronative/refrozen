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

#ifdef REFROZEN_DYNAMIC_MODULE
#include <dlfcn.h>

#include <fstream>
#endif

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
  // Settings game.dll keeps as DWORDs. seenintromovie: the intro has been
  // seen, so it is not played (it needs DirectShow, blizzard.ax). Gfx
  // OpenGL: the game's own OpenGL renderer instead of Direct3D 8.
  g.registry_dwords.push_back({std::string("HKCU\\") + kWar3Key + "\\Misc", "seenintromovie", 1});
  g.registry_dwords.push_back({std::string("HKCU\\") + kWar3Key, "Gfx OpenGL", 1});
  g.lifted_dlls = {
      {"msvcr80.dll"},  // imported by war3.exe, game.dll, Storm.dll
      {"Storm.dll"},    // imported by war3.exe and game.dll (by ordinal)
      {"Mss32.dll"},    // imported by war3.exe and game.dll
      {"ijl15.dll"},    // Intel JPEG Library, imported by game.dll (by ordinal)
      {"game.dll"},     // LoadLibrary'd by war3.exe
      {"redist\\miles\\Mp3dec.asi"},  // Miles providers, LoadLibrary'd by Mss32
      {"redist\\miles\\Mssfast.m3d"},
      {"redist\\miles\\Msseax2.m3d"},
      {"redist\\miles\\Mssdolby.m3d"},
      {"redist\\miles\\Reverb3.flt"},
  };
  return g;
}

#ifdef REFROZEN_DYNAMIC_MODULE
// The game module: the player's own game code, lifted and compiled on this
// Mac by the first-run builder (scripts/poc/build_module.sh). Its function
// table registers itself when it is loaded. It must come from the same
// reFrozen build as this launcher: its stamp file is checked before any of
// its code runs, and its stamp symbol after loading.
bool LoadGameModule(const std::string& path) {
  const std::filesystem::path dir = std::filesystem::path(path).parent_path();
  std::string stamp;
  std::ifstream(dir / "stamp.txt") >> stamp;
  if (stamp != REFROZEN_MODULE_STAMP) {
    std::fprintf(stderr, "refrozen: the game module %s is %s, this reFrozen needs %s: "
                         "rebuild it\n", path.c_str(), stamp.empty() ? "missing or unstamped"
                         : ("from build " + stamp).c_str(), REFROZEN_MODULE_STAMP);
    return false;
  }
  void* module = dlopen(path.c_str(), RTLD_NOW | RTLD_LOCAL);
  if (!module) {
    std::fprintf(stderr, "refrozen: cannot load the game module: %s\n", dlerror());
    return false;
  }
  const auto* symbol = static_cast<const char* const*>(dlsym(module, "refrozen_module_stamp"));
  if (!symbol || std::string(*symbol) != REFROZEN_MODULE_STAMP) {
    std::fprintf(stderr, "refrozen: the game module %s does not match its stamp file: "
                         "rebuild it\n", path.c_str());
    return false;
  }
  return true;
}

std::string DataFolder() {
  const char* home = std::getenv("HOME");
  return std::string(home ? home : "") + "/Library/Application Support/reFrozen";
}

std::string DefaultModule() { return DataFolder() + "/build/current/war3.dylib"; }
#endif

}  // namespace

int main(int argc, char** argv) {
  const char* env = std::getenv("REFROZEN_GAME_DIR");
#ifdef REFROZEN_DYNAMIC_MODULE
  std::string game_dir = env ? env : DataFolder() + "/game";
#else
  std::string game_dir = env ? env : REFROZEN_DEFAULT_GAME_DIR;
#endif
  std::string args;
#ifdef REFROZEN_DYNAMIC_MODULE
  const char* module_env = std::getenv("REFROZEN_MODULE");
  std::string module = module_env ? module_env : DefaultModule();
#endif
  for (int i = 1; i < argc; i++) {
    std::string a = argv[i];
    if (a == "--game" && i + 1 < argc) {
      game_dir = argv[++i];
      continue;
    }
#ifdef REFROZEN_DYNAMIC_MODULE
    if (a == "--module" && i + 1 < argc) {
      module = argv[++i];
      continue;
    }
#endif
    args += (args.empty() ? "" : " ") + a;
  }
  const std::filesystem::path exe = std::filesystem::path(game_dir) / "war3.exe";
  if (!std::filesystem::is_regular_file(exe)) {
    std::fprintf(stderr, "refrozen: %s not found (install with scripts/native_install.py, "
                         "or pass --game <install dir>)\n", exe.c_str());
    return 2;
  }
#ifdef REFROZEN_DYNAMIC_MODULE
  if (!LoadGameModule(module)) return 3;
#endif
  return recomp::RunProcess(Config(), exe.string(), game_dir, args);
}
