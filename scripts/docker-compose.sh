#!/bin/bash

set -e
cd "$(dirname -- "$0")/.."

finish() {
    rm ./workspace/docker-compose-services.yaml 2> /dev/null || true
}
trap finish EXIT

mkdir -p workspace

./scripts/gen-dc-for-services.sh > ./workspace/docker-compose-services.yaml

sudo docker-compose -f docker-compose.yaml -f ./workspace/docker-compose-services.yaml "$@"
