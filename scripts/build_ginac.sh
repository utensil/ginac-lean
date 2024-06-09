#!/usr/bin/env bash

set -euo pipefail
set -v

echo "Building GiNaC"

SCRIPTS_DIR=$(cd $(dirname $(echo "$0")) && pwd)
# patch SCRIPTS_DIR on Windows CI
# if [ "$RUNNER_OS" == "Windows" ]; then
#     SCRIPTS_DIR=$(cd "./scripts" && pwd)
# fi
source $SCRIPTS_DIR/config.sh

cd $WORKSPACES

download https://www.ginac.de/$LIBGINAC.tar.bz2

export CC="clang"
export CXX="clang++"

cd $LIBGINAC

export CLN_CFLAGS="-I$INSTALLED_DIR/include"
export CLN_LIBS="-L$INSTALLED_DIR/lib -lcln"

export CPPFLAGS=""

# patch configure on Windows CI
if [ "$RUNNER_OS" == "Windows" ]; then
    sed -i -E "/as_fn_error \$\? \"expected an absolute directory name for --\$ac_var: \$ac_val\"/d" ./configure
fi

./configure  --prefix=$INSTALLED_DIR

# export CPPFLAGS="-stdlib=libc++"

make -j8

make install

# -###
clang++ -x c++ -E -std=c++11 -stdlib=libc++ - -v < /dev/null 2>&1

echo Add the following to your ~/.profile or similar files that applies to your shell
echo export PATH=$INSTALLED_DIR/bin:$PATH
