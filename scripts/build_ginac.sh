#!/bin/bash

set -e
set -o pipefail

SCRIPTS_DIR=$(cd $(dirname "$0") && pwd)
# echo "SCRIPTS_DIR=$SCRIPTS_DIR"
WORKSPACES="$SCRIPTS_DIR/../build"
mkdir -p $WORKSPACES/
WORKSPACES=$(cd $WORKSPACES && pwd)
# echo "WORKSPACES=$WORKSPACES"
INSTALLED_DIR=$WORKSPACES
mkdir -p $INSTALLED_DIR/
# echo "INSTALLED_DIR=$INSTALLED_DIR"

show_warning()
{
    echo -e "\e[31mWARN\e[0m" "$@"
}

show_info()
{
    echo -e "\e[34mINFO\e[0m" "$@"
}

show_debug()
{
    echo -e "\e[90mDEBUG\e[0m" "$@"
}

show_ok()
{
    echo -e "\e[32mOK\e[0m" "$@"
}

download()
{
    URL=$1
    TAR=$(basename "$URL")
    DIR=${2:-${TAR%.t*}}

    if [ ! -f "$WORKSPACES/$TAR" ]; then
        echo "Downloading to $WORKSPACES/$TAR"
        wget --no-check-certificate "$URL" -O "$WORKSPACES/$TAR"
    else
        echo "Found downloaded $WORKSPACES/$TAR"
    fi

    if [ ! -d "$WORKSPACES/$DIR" ]; then
        echo "Extracting to "$WORKSPACES/$DIR", this may take a while..."
        tar -xf "$WORKSPACES/$TAR" -C $WORKSPACES/
    else
        echo "Found extracted $WORKSPACES/$DIR"
    fi

    # declare -g INSTALLED_DIR="$WORKSPACES/$DIR"
}

mkdir -p $WORKSPACES
cd $WORKSPACES

LIBCLN=cln-1.3.6

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

./configure --prefix=$INSTALLED_DIR

export CPPFLAGS="-DNO_ASM" # -stdlib=libc++"

make -j8 V=1

make check -j4

make install

cd $WORKSPACES

download https://www.ginac.de/ginac-1.8.7.tar.bz2

cd ginac-1.8.7

export CLN_CFLAGS="-I$INSTALLED_DIR/include"
export CLN_LIBS="-L$INSTALLED_DIR/lib -lcln"

export CPPFLAGS=""

./configure  --prefix=$INSTALLED_DIR

# export CPPFLAGS="-stdlib=libc++"

make -j8

make check -j4

make install

# -###
clang++ -x c++ -E -std=c++11 -stdlib=libc++ - -v < /dev/null 2>&1

echo Add the following to your ~/.profile or similar files that applies to your shell
echo export PATH=$INSTALLED_DIR/bin:$PATH
