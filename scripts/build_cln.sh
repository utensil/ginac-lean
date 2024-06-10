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

cd $LIBCLN

# On mac, `arch -x86_64 bash scripts/build_ginac.sh` gets further but still fails

# Fix issues on Mac M1
# inspired by https://www.ginac.de/pipermail/cln-list/2021-April/000793.html
# created by diff -u src/base/low/cl_low_div_old.cc src/base/low/cl_low_div.cc > cl_low_div.patch
patch -N src/base/low/cl_low_div.cc < $SCRIPTS_DIR/cl_low_div.patch || true
# created by diff -u src/base/low/cl_low_mul_old.cc src/base/low/cl_low_mul.cc > cl_low_mul.patch
patch -N src/base/low/cl_low_mul.cc < $SCRIPTS_DIR/cl_low_mul.patch || true

if [ "$RUNNER_OS" == "Windows" ]; then
    # https://github.com/mstorsjo/llvm-mingw?tab=readme-ov-file#known-issues
    patch -N build-aux/ltmain.sh < $SCRIPTS_DIR/fix-linker-scripts-for-mingw.patch || true
    patch -N m4/libtool.m4 < $SCRIPTS_DIR/fix-linker-scripts-for-mingw.patch || true
fi

# error: macho does not support linking multiple objects into one

export CPPFLAGS=""

patch_configure

./configure --prefix=$INSTALLED_DIR --enable-shared --enable-static $EXTRA_CONFIGURE_FLAGS

patch_libtool

export CPPFLAGS="-DNO_ASM" # -stdlib=libc++"

if [ "$RUNNER_OS" == "Windows" ]; then
    # https://docs.binarybuilder.org/dev/troubleshooting/#Libtool-refuses-to-build-shared-library-because-of-undefined-symbols
    make -j8 V=1 LDFLAGS="-no-undefined"
else
    make -j8 V=1
fi

make install

echo Add the following to your ~/.profile or similar files that applies to your shell
echo export PATH=$INSTALLED_DIR/bin:$PATH
