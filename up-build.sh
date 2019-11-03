#!/bin/bash

set -e
cd "$(dirname -- "$0")"
DIR=$(pwd)

mkdir -p workspace/services

update-repo() {
    if [ -d "$2" ]; then
        git -C "$2" remote -v
        git -C "$2" checkout .
        git -C "$2" pull --ff-only
    else
        git clone --depth=1 "$1/$2.git"
    fi
}

for FILE in services/*.conf; do (
    NAME=$(basename -- "$FILE")
    NAME=${NAME%.conf}
    . "$FILE"

    cd "$DIR/workspace/services"

    if [[ -n "$REPO_HOST" ]]; then update-repo "$REPO_HOST" "$REPO_NAME"; fi
); done

./scripts/docker-compose.sh up -d --remove-orphans --build
