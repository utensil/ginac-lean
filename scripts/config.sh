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