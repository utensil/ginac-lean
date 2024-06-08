set -e
set -o pipefail

SCRIPTS_DIR=$(cd $(dirname "$0") && pwd)
# echo "SCRIPTS_DIR=$SCRIPTS_DIR"
WORKSPACES="$SCRIPTS_DIR/../.lake/build"
mkdir -p $WORKSPACES/
WORKSPACES=$(cd $WORKSPACES && pwd)
# echo "WORKSPACES=$WORKSPACES"
INSTALLED_DIR=$WORKSPACES
mkdir -p $INSTALLED_DIR/
# echo "INSTALLED_DIR=$INSTALLED_DIR"

export LIBCLN=cln-1.3.7
export LIBGINAC=ginac-1.8.7

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