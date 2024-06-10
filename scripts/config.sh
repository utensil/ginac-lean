#!/usr/bin/env bash
set -euo pipefail
set -v

SCRIPTS_DIR=$(cd $(dirname $(echo "$0")) && pwd)
# patch SCRIPTS_DIR on Windows CI
# if [ "$RUNNER_OS" == "Windows" ]; then
#     SCRIPTS_DIR=$(cd "./scripts" && pwd)
# fi
echo "SCRIPTS_DIR=$SCRIPTS_DIR"
WORKSPACES="$SCRIPTS_DIR/../.lake/build"
# if [ "$RUNNER_OS" == "Windows" ]; then
#     WORKSPACES=".lake/build"
# else
#     mkdir -p $WORKSPACES
# fi
mkdir -p $WORKSPACES

WORKSPACES=$(cd $WORKSPACES && pwd)
echo "WORKSPACES=$WORKSPACES"
INSTALLED_DIR=$WORKSPACES
# if [ "$RUNNER_OS" == "Windows" ]; then
#     INSTALLED_DIR=$WORKSPACES
# else
#     mkdir -p $INSTALLED_DIR/
# fi
mkdir -p $INSTALLED_DIR/

echo "INSTALLED_DIR=$INSTALLED_DIR"

export LIBCLN=cln-1.3.7
export LIBGINAC=ginac-1.8.7

# fix unbounded variable
RUNNER_OS=${RUNNER_OS:-""}

export CC="clang"
export CXX="clang++"

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
        curl -L -o "$WORKSPACES/$TAR" "$URL"
        # wget --no-check-certificate "$URL" -O "$WORKSPACES/$TAR"
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

patch_configure()
{
    # patch configure on Windows CI
    if [ "$RUNNER_OS" == "Windows" ]; then
        # https://github.com/msys2/MINGW-packages/discussions/7589#discussioncomment-261679
        autoreconf -fiv
        # Bypass: configure: error: expected an absolute directory name for --prefix: 0
        sed -i -E "/as_fn_error \$\? \"expected an absolute directory name for --\$ac_var: \$ac_val\"/d" ./configure
        export LDFLAGS="-Wl,-no-undefined"
    fi
}

patch_libtool()
{
    # patch libtool
    # https://stackoverflow.com/questions/61215047/how-to-fix-libtool-undefined-symbols-not-allowed-in-x86-64-pc-msys-shared
    sed -i.bak -e "s/\(allow_undefined=\)yes/\1no/" libtool
}