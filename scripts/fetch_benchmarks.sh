#!/usr/bin/env bash
set -e

DEST=${1:-benchmarks/polybench}

mkdir -p "$(dirname "$DEST")"

git clone --depth 1 \
  https://github.com/sabitov-kirill/polybench-c-cmake.git \
  "$DEST"