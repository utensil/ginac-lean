#!/bin/bash

set -e
set -o pipefail

SCRIPTS_DIR=$(cd $(dirname $(echo "$0")) && pwd)
# patch SCRIPTS_DIR on Windows CI
if [ "$RUNNER_OS" == "Windows" ]; then
    SCRIPTS_DIR=$(cd "./scripts" && pwd)
fi
source $SCRIPTS_DIR/config.sh

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
