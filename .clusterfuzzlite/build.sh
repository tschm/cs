#!/bin/bash -eu
# ClusterFuzzLite build script — installs the package so the frozen harness can
# import the project's runtime dependencies, then compiles each Python harness
# in tests/fuzz/ via OSS-Fuzz's compile_python_fuzzer helper.

cd "$SRC"

# Pin pip so the build environment is reproducible and only changes through a
# reviewed bump (the same rationale as the SHA-pinned base image).
pip3 install --upgrade "pip==24.3.1"

# Install the project and its runtime deps (numpy/polars/jquantstats/tinycta)
# into the build image so PyInstaller can discover and bundle them into each
# frozen fuzz binary. This repo is not src-layout: the importable signal modules
# are flat files under book/marimo/notebooks, which the harness puts on sys.path.
pip3 install .

for fuzzer in tests/fuzz/fuzz_*.py; do
  compile_python_fuzzer "$fuzzer"
done
