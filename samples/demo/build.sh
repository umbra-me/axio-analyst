#!/usr/bin/env sh
# Build the Axio Analyst demo as a native Release executable on macOS or Linux.
# The counterpart of build.ps1: same source, same CMake project, a Mach-O or
# ELF binary instead of a PE. Generated files stay under build/.
set -eu

source_dir=$(cd "$(dirname "$0")" && pwd)
build_dir="$source_dir/build"

# Ninja when present, otherwise the default generator. Both are single-config,
# so the executable lands directly under build/ rather than build/Release/.
if command -v ninja >/dev/null 2>&1; then
  generator="-G Ninja"
else
  generator=""
fi

# shellcheck disable=SC2086
cmake -S "$source_dir" -B "$build_dir" $generator -DCMAKE_BUILD_TYPE=Release
cmake --build "$build_dir"

executable="$build_dir/axio_analyst_demo"
if [ ! -f "$executable" ]; then
  echo "Build completed without the expected executable: $executable" >&2
  exit 1
fi

echo "$executable"
