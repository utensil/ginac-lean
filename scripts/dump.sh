#!/usr/bin/env bash

set -euo pipefail
# set -v

SCRIPTS_DIR=$(cd $(dirname "$0") && pwd)
source $SCRIPTS_DIR/config.sh

INCLUDE_PATH=$WORKSPACES/include

header=${1:-"ginac/symbol.h"}

header_full=$INCLUDE_PATH/$header
output_dir=codegen/tests/fixtures
output_file=$output_dir/$(echo $header|sed -E 's/[^A-Za-z0-9]+/-/g')

if [ ! -f $output_file ]; then
    echo "Dumping AST: $header_full -> $output_file.json"
    clang -w -x c++ -std=c++14 -Xclang -ast-dump=json -fsyntax-only -fno-diagnostics-color -I$INCLUDE_PATH $header_full > $output_file.json
fi

# brew install jaq

# jaq '.inner|length' $output_file.json

echo "Shortening AST: $output_file.json -> $output_file-short.json"

# -c for compact output
jaq -f $SCRIPTS_DIR/dump.jq $output_file.json > $output_file-short.json

