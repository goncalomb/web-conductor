#!/bin/bash

set -e
shopt -s nullglob

cd "$(dirname -- "$0")/.."
DIR=$(pwd)

echo 'version: "3.7"'

FIRST=
for FILE in services/*.conf; do
    if [ -z "$FIRST" ]; then
        FIRST=1
        echo
        echo 'services:'
    fi

    NAME=$(basename -- "$FILE")
    NAME=${NAME%.conf}
    . "$FILE"

    echo "  $NAME:"
    echo "    build:"
    echo "      context: \"$DIR/workspace/services/$REPO_NAME\""
    echo "      dockerfile: \"$DIR/services/$NAME.dockerfile\""

    echo "    restart: always"

    echo "    labels:"
    echo "      - \"traefik.enable=true\""
    echo "      - \"traefik.http.routers.$NAME-http.entryPoints=http\""
    echo "      - \"traefik.http.routers.$NAME-http.rule=Host(\`$HOST\`)\""
    echo "      - \"traefik.http.routers.$NAME-http.middlewares=302https@file"\"
    echo "      - \"traefik.http.routers.$NAME-https.entryPoints=https\""
    echo "      - \"traefik.http.routers.$NAME-https.rule=Host(\`$HOST\`)\""
    echo "      - \"traefik.http.routers.$NAME-https.middlewares=302https@file"\"
    echo "      - \"traefik.http.routers.$NAME-https.tls"\"
done
