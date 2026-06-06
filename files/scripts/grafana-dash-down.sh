#!/usr/bin/env bash

set -euo pipefail
cd -- "$(dirname -- "$0")/.."

if [ "$#" -lt 1 ]; then
    echo "usage: ${0##*/} <id> [id]..." >&2
    exit 1
fi

# download grafana dashboards
# print messages to stderr, print changes to stdout (for ansible changed_when)

docker compose exec -T grafana bash -s -- "$@" <<'EOF'
set -euo pipefail
set +x

for V in "$@"; do
    # TODO: replace dashboard file if doing a revision update
    FILE="/var/lib/grafana/dashboards/$V.json"
    URL="https://grafana.com/api/dashboards/${V%-*}/revisions/${V##*-}/download"
    if [ -f "$FILE" ]; then
        continue
    fi
    curl --create-dirs -f#RLo "$FILE" "$URL"
    # https://github.com/grafana/grafana/issues/10786
    sed -i "s/\${DS_PROMETHEUS}//g" "$FILE"
    echo "$FILE"
done
EOF
