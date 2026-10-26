#!/bin/bash
# Release dependencies built from checksum-pinned sources (never Homebrew's):
# what the app ships or links. Offline: the archives are fetched beforehand
# into <src> and checked against these SHA-256s (from Homebrew's formulae
# for the same versions, a second source).
#
#   scripts/release/build_deps.sh <src dir> <prefix>
#
# SDL3 and StormLib are shared libraries (install name @rpath/..., shipped in
# the app); glslang, SPIRV-Tools and SPIRV-Cross are static (linked into the
# runtime); LLVMDemangle is built from llvm/lib/Demangle only. Everything
# targets arm64, macOS 14.
set -euo pipefail
SRC=$(cd "$1" && pwd) PREFIX=$2
mkdir -p "$PREFIX" && PREFIX=$(cd "$PREFIX" && pwd)
WORK="$PREFIX/.work"
JOBS=$(sysctl -n hw.ncpu)
COMMON=(-G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PREFIX"
  -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=14.0
  -DCMAKE_INSTALL_NAME_DIR=@rpath -DCMAKE_PREFIX_PATH="$PREFIX"
  -DCMAKE_IGNORE_PREFIX_PATH=/opt/homebrew -DCMAKE_FIND_FRAMEWORK=LAST
  "-DCMAKE_C_FLAGS=-ffile-prefix-map=$PREFIX=deps" "-DCMAKE_CXX_FLAGS=-ffile-prefix-map=$PREFIX=deps")

pins() {
  cat <<'EOF'
SDL3-3.4.18.tar.gz 9c75cf16330322c217dedd2e0609f1124f1b54b8633e763467b4684d0f4334a3
glslang-16.6.0.tar.gz 9c09b901149c729df745057dafa815278aaa101b84d2b6e14f16a42de52f97f2
spirv-tools-vulkan-sdk-1.4.363.0.tar.gz e6c83a215538fbfd265ccf398d3877985055df1273dbed73912bd05307664688
spirv-headers-vulkan-sdk-1.4.363.0.tar.gz 5b3a0d099f5c7649e29c0938476c462e71d66ad89a0bde42fa1ba3eb476956c9
spirv-cross-vulkan-sdk-1.4.363.0.tar.gz f708982e88b763ef5b0394ed468fc2c3628f68cdab89f2e7a946cd628c04e721
stormlib-v9.40.tar.gz f80b08bae168888702a4251312d6c2279f487673df611c2b5ef4f395e810c3b1
llvm-project-23.1.4.src.tar.xz 819ecf7351f1a66f76b2d701d8942faaf5faeb324cb90c9d5b090de142434bb2
EOF
}

rm -rf "$WORK" && mkdir -p "$WORK"
while read -r file sha; do
  f=$(ls "$SRC" | grep -F -- "${file}" | head -1)
  [ -n "$f" ] || { echo "missing source: $file" >&2; exit 1; }
  [ "$(shasum -a 256 "$SRC/$f" | cut -c1-64)" = "$sha" ] || { echo "checksum mismatch: $f" >&2; exit 1; }
  echo "verified $f"
done < <(pins)

unpack() {  # archive pattern -> directory
  local f d
  f=$(ls "$SRC" | grep -F -- "$1" | head -1)
  d="$WORK/$(echo "$1" | cut -d. -f1)"
  mkdir -p "$d" && tar -xf "$SRC/$f" -C "$d" --strip-components 1 ${2:-}
  echo "$d"
}

licence() {  # source dir, name: its licence files into licenses/<name>
  mkdir -p "$PREFIX/licenses/$2"
  find "$1" -maxdepth 2 -type f \( -iname "LICENSE*" -o -iname "COPYING*" -o -iname "NOTICE*" \) \
    -exec cp {} "$PREFIX/licenses/$2/" \;
}

build() {  # source dir, extra cmake args...
  local s=$1; shift
  cmake -S "$s" -B "$s/_build" "${COMMON[@]}" "$@" > "$s/configure.log"
  cmake --build "$s/_build" -j "$JOBS" > "$s/build.log"
  cmake --install "$s/_build" > "$s/install.log"
}

S=$(unpack SDL3-3.4.18)
build "$S" -DSDL_SHARED=ON -DSDL_STATIC=OFF -DSDL_TEST_LIBRARY=OFF -DSDL_TESTS=OFF -DSDL_EXAMPLES=OFF
licence "$S" SDL3
echo "built SDL3"
H=$(unpack spirv-headers-vulkan-sdk)
build "$H"
T=$(unpack spirv-tools-vulkan-sdk)
build "$T" -DSPIRV-Headers_SOURCE_DIR="$H" -DSPIRV_SKIP_TESTS=ON -DSPIRV_SKIP_EXECUTABLES=ON -DSPIRV_WERROR=OFF \
  -DBUILD_SHARED_LIBS=OFF
licence "$H" SPIRV-Headers
licence "$T" SPIRV-Tools
echo "built SPIRV-Tools"
G=$(unpack glslang-16.6.0)
build "$G" -DBUILD_SHARED_LIBS=OFF -DGLSLANG_TESTS=OFF -DENABLE_OPT=ON -DALLOW_EXTERNAL_SPIRV_TOOLS=ON \
  -DENABLE_GLSLANG_BINARIES=ON
licence "$G" glslang
echo "built glslang"
C=$(unpack spirv-cross-vulkan-sdk)
build "$C" -DSPIRV_CROSS_SHARED=OFF -DSPIRV_CROSS_STATIC=ON -DSPIRV_CROSS_CLI=ON -DSPIRV_CROSS_ENABLE_TESTS=OFF
licence "$C" SPIRV-Cross
echo "built SPIRV-Cross"
M=$(unpack stormlib-v9.40)
# A shared StormLib is always a framework on macOS, installed to /Library/Frameworks:
# take its library out of the build as libstorm.dylib instead.
build_only() { cmake -S "$1" -B "$1/_build" "${COMMON[@]}" "${@:2}" > "$1/configure.log"; cmake --build "$1/_build" -j "$JOBS" > "$1/build.log"; }
build_only "$M" -DBUILD_SHARED_LIBS=ON -DSTORM_BUILD_TESTS=OFF -DSTORM_SKIP_INSTALL=ON
cp "$(find "$M/_build/storm.framework/Versions" -type f -name storm | head -1)" "$PREFIX/lib/libstorm.dylib"
install_name_tool -id @rpath/libstorm.dylib "$PREFIX/lib/libstorm.dylib"
licence "$M" StormLib
echo "built StormLib"
L=$(unpack llvm-project-23.1.4 "--include=*/llvm/lib/Demangle/* --include=*/llvm/include/llvm/Demangle/* --include=*/llvm/LICENSE.TXT")
mkdir -p "$L/_build" "$PREFIX/lib" "$PREFIX/include/llvm/Config"
# The Demangle headers read one setting from LLVM's generated llvm-config.h,
# LLVM_ENABLE_LLVM_EXPORT_ANNOTATIONS, which a static library leaves unset.
mkdir -p "$L/llvm/include/llvm/Config"
printf '%s\n' '/* reFrozen: the part of llvm-config.h that llvm/Demangle reads (a static' \
  '   LLVMDemangle: LLVM_ENABLE_LLVM_EXPORT_ANNOTATIONS stays undefined). */' \
  > "$L/llvm/include/llvm/Config/llvm-config.h"
cp "$L/llvm/include/llvm/Config/llvm-config.h" "$PREFIX/include/llvm/Config/"
for c in "$L"/llvm/lib/Demangle/*.cpp; do
  /usr/bin/xcrun clang++ -std=c++17 -O2 -arch arm64 -mmacosx-version-min=14.0 -I "$L/llvm/include" \
    -ffile-prefix-map="$L"=llvm -c "$c" -o "$L/_build/$(basename "${c%.cpp}").o"
done
/usr/bin/xcrun ar rcs "$PREFIX/lib/libLLVMDemangle.a" "$L"/_build/*.o
cp -R "$L/llvm/include/llvm/Demangle" "$PREFIX/include/llvm/"
mkdir -p "$PREFIX/licenses/LLVM" && cp "$L/llvm/LICENSE.TXT" "$PREFIX/licenses/LLVM/"
echo "built LLVMDemangle"
rm -rf "$WORK"
echo "deps: $PREFIX"
