#!/bin/bash

set -e
shopt -s nullglob

cd "$(dirname -- "$0")"
DIR=$(pwd)

mkdir -p workspace/services

update-repo() {
    if [ -d "$2" ]; then
        echo "Updating repo '$2'..."
        git -C "$2" remote -v
        # checkout + GIT_MTIME invalidates docker cache (COPY . .) if .dockerignore is not setup properly :(
        # more research is needed
        # git -C "$2" checkout .
        # also, docker cache ignores mtime changes, build with --no-cache (once) when setting GIT_MTIME
        # https://github.com/moby/moby/pull/12031
        # https://github.com/moby/moby/blob/master/pkg/tarsum/tarsum_spec.md
        if [ -n "$GIT_MTIME" ] && [ "$(git -C "$2" rev-parse --is-shallow-repository)" == "true" ]; then
            git -C "$2" pull --ff-only --unshallow
        else
            git -C "$2" pull --ff-only
        fi
    elif [ -n "$GIT_MTIME" ]; then
        echo "Cloning repo '$2' (full)..."
        git clone "$1/$2.git"
    else
        echo "Cloning repo '$2' (depth=1)..."
        git clone --depth=1 "$1/$2.git"
    fi

    if [ -n "$GIT_MTIME" ]; then (
        echo "Touching files (git modified dates)..."
        cd "$2"
        git ls-tree -r -t HEAD --name-only | while IFS= read -r f; do
            t=$(git log -n 1 --format="%ct" -- "$f")
            [ -n "$t" ] && touch -m -d "@$t" "$f"
        done
    ); fi
}

service-update-repo() {(
    GIT_MTIME=
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
