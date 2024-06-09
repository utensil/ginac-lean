#!/usr/bin/env bash

set -euo pipefail
set -v

echo "Building CLN"

SCRIPTS_DIR=$(cd $(dirname $(echo "$0")) && pwd)
# patch SCRIPTS_DIR on Windows CI
# if [ "$RUNNER_OS" == "Windows" ]; then
#     SCRIPTS_DIR=$(cd "./scripts" && pwd)
# fi
source $SCRIPTS_DIR/config.sh

cd $WORKSPACES

download https://www.ginac.de/CLN/$LIBCLN.tar.bz2

export CC="clang"
export CXX="clang++"

cd $LIBCLN

# On mac, `arch -x86_64 bash scripts/build_ginac.sh` gets further but still fails

# Fix issues on Mac M1
# inspired by https://www.ginac.de/pipermail/cln-list/2021-April/000793.html
# created by diff -u src/base/low/cl_low_div_old.cc src/base/low/cl_low_div.cc > cl_low_div.patch
patch -N src/base/low/cl_low_div.cc < $SCRIPTS_DIR/cl_low_div.patch || true
# created by diff -u src/base/low/cl_low_mul_old.cc src/base/low/cl_low_mul.cc > cl_low_mul.patch
patch -N src/base/low/cl_low_mul.cc < $SCRIPTS_DIR/cl_low_mul.patch || true

# error: macho does not support linking multiple objects into one

export CPPFLAGS=""

# patch configure on Windows CI
if [ "$RUNNER_OS" == "Windows" ]; then
    sed -i -E "/as_fn_error \$\? \"expected an absolute directory name for --\$ac_var: \$ac_val\"/d" ./configure
fi

export LDFLAGS="-Wl,-no-undefined"

./configure --prefix=$INSTALLED_DIR

# patch libtool
# https://stackoverflow.com/questions/61215047/how-to-fix-libtool-undefined-symbols-not-allowed-in-x86-64-pc-msys-shared
sed -i.bak -e "s/\(allow_undefined=\)yes/\1no/" libtool

export CPPFLAGS="-DNO_ASM" # -stdlib=libc++"

make -j8 V=1

make install

echo Add the following to your ~/.profile or similar files that applies to your shell
echo export PATH=$INSTALLED_DIR/bin:$PATH
