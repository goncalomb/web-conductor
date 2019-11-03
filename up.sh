#!/bin/bash

set -e
cd "$(dirname -- "$0")"

./scripts/docker-compose.sh up -d --remove-orphans
