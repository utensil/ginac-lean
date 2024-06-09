#!/bin/bash

set -e
set -o pipefail

echo "Building GiNaC"

source $(dirname $(echo "$0"))/config.sh

mkdir -p $WORKSPACES
cd $WORKSPACES

download https://www.ginac.de/$LIBGINAC.tar.bz2

cd $LIBGINAC

export CLN_CFLAGS="-I$INSTALLED_DIR/include"
export CLN_LIBS="-L$INSTALLED_DIR/lib -lcln"

export CPPFLAGS=""

# patch configure on Windows CI
if [ "$RUNNER_OS" == "Windows" ]; then
    sed -i -E "/expected an absolute directory name/d" ./configure
fi

./configure  --prefix=$INSTALLED_DIR

# export CPPFLAGS="-stdlib=libc++"

make -j8

make install

# -###
clang++ -x c++ -E -std=c++11 -stdlib=libc++ - -v < /dev/null 2>&1

echo Add the following to your ~/.profile or similar files that applies to your shell
echo export PATH=$INSTALLED_DIR/bin:$PATH
