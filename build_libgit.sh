#!/bin/sh
set -e
. virtualenv/bin/activate
mkdir -p build
cd build
cmake ../libgit -DCMAKE_INSTALL_PREFIX=../virtualenv/local
cmake --build .
make install
