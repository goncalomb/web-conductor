#!/bin/bash

set -e
cd "$(dirname -- "$0")/.."
DIR=$(pwd)

echo 'version: "3.7"'
echo
echo 'services:'

for FILE in services/*.conf; do
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
    echo "      - \"traefik.http.routers.$NAME-http.rule=Host(\`$HOST.local\`)\""
    echo "      - \"traefik.http.routers.$NAME-https.entryPoints=https\""
    echo "      - \"traefik.http.routers.$NAME-https.rule=Host(\`$HOST.local\`)\""
    echo "      - \"traefik.http.routers.$NAME-https.tls"\"
done
