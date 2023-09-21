#!/bin/bash

sudo apt update
sudo apt install -y curl wget git git-lfs clang lld libc++-dev
sudo apt install -y libunwind-dev || true

curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | bash -s -- -y
source ~/.profile