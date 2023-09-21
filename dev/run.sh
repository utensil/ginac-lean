#!/bin/bash
sudo docker exec -it -u vscode -w /workspaces/ginac-lean ginac-lean bash

# First time: run this in the container
# source dev/prep.sh