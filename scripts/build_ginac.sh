#!/usr/bin/env bash

set -euo pipefail
# set -v

echo "Building GiNaC"

SCRIPTS_DIR=$(cd $(dirname "$0") && pwd)
source $SCRIPTS_DIR/config.sh

cd $WORKSPACES

download https://www.ginac.de/$LIBGINAC.tar.bz2

cd $LIBGINAC

export CLN_CFLAGS="-I$INSTALLED_DIR/include"
export CLN_LIBS="-L$INSTALLED_DIR/lib -lcln"

export CPPFLAGS=""

patch_configure

./configure  --prefix=$INSTALLED_DIR --enable-shared --enable-static $EXTRA_CONFIGURE_FLAGS

patch_libtool

# export CPPFLAGS="-stdlib=libc++"

make -j8

make install

if [ "$RUNNER_OS" == "Windows" ]; then
    cp $INSTALLED_DIR/bin/libginac-11.dll $INSTALLED_DIR/lib/ginac.dll
fi

# -###
clang++ -x c++ -E -std=c++11 -stdlib=libc++ - -v < /dev/null 2>&1

echo Add the following to your ~/.profile or similar files that applies to your shell
echo export PATH=$INSTALLED_DIR/bin:$PATH
