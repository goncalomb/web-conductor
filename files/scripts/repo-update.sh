#!/usr/bin/env bash

set -euo pipefail
cd -- "$(dirname -- "$0")/.."

if [ "$#" -ne 2 ]; then
    echo "usage: ${0##*/} <name> <url>" >&2
    echo "  GIT_MTIME=1  set file mtimes from git dates" >&2
    exit 1
fi

# update workspace service repositories
# print messages to stderr, print changes to stdout (for ansible changed_when)

GIT_MTIME="${GIT_MTIME:-}"

mkdir -p workspace/services
cd workspace/services

repo-update() {
    if [ -d "$2" ]; then
        # TODO: update remote url if changed
        git -C "$2" remote -v >&2
        HEAD_REF=$(git -C "$2" rev-parse HEAD)
        # checkout + GIT_MTIME invalidates docker cache (COPY . .) if .dockerignore is not setup properly :(
        # more research is needed
        # git -C "$2" checkout .
        # also, docker cache ignores mtime changes, build with --no-cache (once) when setting GIT_MTIME
        # https://github.com/moby/moby/pull/12031
        # https://github.com/moby/moby/blob/master/pkg/tarsum/tarsum_spec.md
        if [ -n "$GIT_MTIME" ] && [ "$(git -C "$2" rev-parse --is-shallow-repository)" == "true" ]; then
            git -C "$2" pull --ff-only --unshallow >&2
        else
            git -C "$2" pull --ff-only >&2
        fi
        if [ "$HEAD_REF" != "$(git -C "$2" rev-parse HEAD)" ]; then
            echo "updated '$2'"
        fi
    elif [ -n "$GIT_MTIME" ]; then
        git clone "$1" "$2"
        echo "cloned '$2' (full)"
    else
        git clone --depth=1 "$1" "$2"
        echo "cloned '$2' (depth=1)"
    fi

    if [ -n "$GIT_MTIME" ]; then
        (
            cd "$2"
            git ls-tree -r -t HEAD --name-only | while IFS= read -r f; do
                gt=$(git log -n 1 --format="%ct" -- "$f")
                st=$(stat -c "%Y" -- "$f")
                if [ -n "$gt" ] && [ "$gt" -ne "$st" ]; then
                    touch -m -d "@$gt" "$f"
                    echo "touched '$2/$f'"
                fi
            done
        )
    fi
}

repo-update "$2" "$1/repo"
