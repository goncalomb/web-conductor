#!/bin/bash

set -e
cd -- "$(dirname -- "$0")"

DASHBOARDS=(
    1860-31 # https://grafana.com/grafana/dashboards/1860-node-exporter-full/
    17346-7 # https://grafana.com/grafana/dashboards/17346-traefik-official-standalone-dashboard/
    4475-5 # https://grafana.com/grafana/dashboards/4475-traefik/
    11462-1 # https://grafana.com/grafana/dashboards/11462-traefik-2/
)

./web-conductor.py compose -- exec grafana mkdir -p /var/lib/grafana/dashboards

for V in ${DASHBOARDS[*]}; do
    ./web-conductor.py compose -- exec grafana \
        wget -O "/var/lib/grafana/dashboards/$V.json" \
        "https://grafana.com/api/dashboards/${V%-*}/revisions/${V##*-}/download"
    # https://github.com/grafana/grafana/issues/10786
    ./web-conductor.py compose -- exec grafana sed -i "s/\${DS_PROMETHEUS}//g" "/var/lib/grafana/dashboards/$V.json"
done
