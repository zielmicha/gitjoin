#!/bin/sh
set -e
git submodule init
git submodule update
. virtualenv/bin/activate
mkdir -p build
cd build
cmake ../libgit -DCMAKE_INSTALL_PREFIX=../virtualenv/local
cmake --build .
make install
