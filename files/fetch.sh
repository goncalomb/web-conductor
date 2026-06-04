#!/usr/bin/env bash

set -euo pipefail
cd -- "$(dirname -- "$0")"

# XXX: this logic should eventually be moved to web-conductor.py, maybe?

eval "$(./web-conductor.py bash)"

mkdir -p workspace/services
cd workspace/services

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
        git clone "$1" "$2"
    else
        echo "Cloning repo '$2' (depth=1)..."
        git clone --depth=1 "$1" "$2"
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
    URL=${WC_REPO_URL[$1]}
    NAME=${WC_SERVICE_NAME[$1]}
    BUILD_CMD=${WC_REPO_BUILD[$1]}
    GIT_MTIME=${WC_REPO_MTIME[$1]}
    if [ -n "$URL" ]; then
        update-repo "$URL" "$NAME/repo" "$BUILD_CMD"
    fi
)}

declare -A S_EN
for NAME in "$@"; do
    S_EN["$NAME"]=1
done

for I in "${!WC_SERVICE_NAME[@]}"; do
    NAME=${WC_SERVICE_NAME[$I]}
    if [ $# -eq 0 ] || [ -n "${S_EN[$NAME]:-}" ]; then
        service-update-repo "$I"
    fi
done
