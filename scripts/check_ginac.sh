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

mkdir -p $WORKSPACES
cd $WORKSPACES

LIBCLN=cln-1.3.6

export CC="clang"
export CXX="clang++"

cd $LIBCLN

make check -j4

cd $WORKSPACES

cd ginac-1.8.7

export CLN_CFLAGS="-I$INSTALLED_DIR/include"
export CLN_LIBS="-L$INSTALLED_DIR/lib -lcln"

export CPPFLAGS=""

make check -j4
