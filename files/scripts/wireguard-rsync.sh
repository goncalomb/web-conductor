#!/usr/bin/env bash

set -euo pipefail
cd -- "$(dirname -- "$0")/.."

# this script is necessary because --rsync-path expects a single command, on a
# normal ssh connection it works without it (the arguments are passed to sh -c),
# but not on DinD (molecule) where -rsh='/usr/bin/docker exec -i' and docker
# exec separates the command from the arguments

exec docker compose exec -T wireguard sh -c 'apk add -q rsync && rsync "$@"' -- "$@"
