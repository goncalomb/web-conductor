#!/bin/bash

set -e
shopt -s nullglob

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

service-update-repo() {(
    . "$1"
    cd "$DIR/workspace/services"
    if [[ -n "$REPO_HOST" ]]; then update-repo "$REPO_HOST" "$REPO_NAME"; fi
)}

if [ -z "$*" ]; then
    for FILE in services/*.conf; do
        service-update-repo "$FILE"
    done
else
    for NAME in "$@"; do
        FILE="services/$NAME.conf"
        if [ -f "$FILE" ]; then
            service-update-repo "$FILE"
        fi
    done
fi

./scripts/docker-compose.sh up -d --remove-orphans --build "$@"
