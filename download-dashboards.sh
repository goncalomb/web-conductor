#!/bin/bash

set -e
cd -- "$(dirname -- "$0")"

DASHBOARDS=(
    1860-31 # https://grafana.com/grafana/dashboards/1860-node-exporter-full/
)

./web-conductor.py compose -- exec grafana mkdir -p /var/lib/grafana/dashboards

for V in ${DASHBOARDS[*]}; do
    ./web-conductor.py compose -- exec grafana \
        wget -O "/var/lib/grafana/dashboards/$V.json" \
        "https://grafana.com/api/dashboards/${V%-*}/revisions/${V##*-}/download"
done
