#!/bin/bash

set -e
set -o pipefail

source $(dirname "$0")/config.sh

mkdir -p $WORKSPACES
cd $WORKSPACES

export CC="clang"
export CXX="clang++"

cd $LIBCLN

make check -j4

cd $WORKSPACES

cd ginac-1.8.7

export CLN_CFLAGS="-I$INSTALLED_DIR/include"
export CLN_LIBS="-L$INSTALLED_DIR/lib -lcln"

export CPPFLAGS=""

export PATH="$WORKSPACES/bin:$PATH"

make check -j4
