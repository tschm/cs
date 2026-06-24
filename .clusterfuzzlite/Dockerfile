# ClusterFuzzLite build image for cs.
# Uses the OSS-Fuzz Python base image, which provides Atheris and the
# compile_python_fuzzer helper. Pinned by SHA256 so the build image only
# changes through reviewed updates.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:9c97273c8de83d22a40462fdda4371d1ff16eac065c72ee03bef7fdb1aaaf458

COPY . $SRC
WORKDIR $SRC
COPY .clusterfuzzlite/build.sh $SRC/build.sh
