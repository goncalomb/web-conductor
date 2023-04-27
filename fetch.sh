#!/bin/bash

set -e
shopt -s nullglob

cd -- "$(dirname -- "$0")"
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
        echo "Touching files..."
        (
            cd "$2"
            # touch using git dates
            git ls-tree -r -t HEAD --name-only | while IFS= read -r f; do
                t=$(git log -n 1 --format="%ct" -- "$f")
                [ -n "$t" ] && touch -m -d "@$t" "$f"
            done
            # touch using .mtimes, this can be dangerous (arbitrary code execution, bad repos)
            if [ -f .mtimes ]; then
                bash .mtimes
            fi
        )
    ); fi

    if [ -n "$3" ]; then
        echo "Running build command..."
        (
            cd "$2"
            "$3" # build command
        )
    fi
}

service-update-repo() {(
    GIT_MTIME=1
    REPO_HOST=${WC_REPO_HOSTS[$1]}
    REPO_NAME=${WC_REPO_NAMES[$1]}
    BUILD_CMD=${WC_BUILD_CMDS[$1]}
    cd "$DIR/workspace/services"
    if [ -n "$REPO_HOST" ]; then
        update-repo "$REPO_HOST" "$REPO_NAME" "$BUILD_CMD"
    fi
)}

DATA=$(./web-conductor.py bash)
eval $DATA

if [ -z "$*" ]; then
    for I in "${!WC_SERVICES[@]}"; do
        service-update-repo "$I"
    done
else
    for NAME in "$@"; do
        for I in "${!WC_SERVICES[@]}"; do
            if [[ "$NAME" == "${WC_SERVICES[$I]}" ]]; then
                service-update-repo "$I"
                break
            fi
        done
    done
fi

./web-conductor.py --sudo up-build "$@"
