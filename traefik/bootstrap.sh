#!/bin/sh

set -e

echo "bootstrap: hi"

SIG=
signal() {
    echo "bootstrap: received signal"
    SIG=1
}
trap signal INT TERM

# create final traefik config file

cp /etc/traefik/traefik-dynamic.orig.toml /etc/traefik/traefik-dynamic.toml

# find Let's Encrypt certs on the volume

LETSENCRYPT_DIR=/etc/letsencrypt/live
if [ -d "$LETSENCRYPT_DIR" ]; then
    echo "bootstrap: searching '/etc/letsencrypt/live' for tls certificates"
    echo >> /etc/traefik/traefik-dynamic.toml
    for FOLDER in "$LETSENCRYPT_DIR"/*; do
        [ -d "$FOLDER" ] || continue
        CERT_FILE="$FOLDER/cert.pem"
        KEY_FILE="$FOLDER/privkey.pem"
        if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
            echo "bootstrap: found tls certificate '$FOLDER'"
            {
                echo "[[tls.certificates]]"
                echo "    certFile = \"$CERT_FILE\""
                echo "    keyFile = \"$KEY_FILE\""
            } >> /etc/traefik/traefik-dynamic.toml
        else
            echo "bootstrap: missing files in '$FOLDER', skipping"
        fi
    done
else
    echo "bootstrap: '/etc/letsencrypt/live' not found, skipping certificate search"
fi

# in addition to traefik, we need syslogd and crond for log rotation
# start everything as background jobs and wait for any to finish

echo "bootstrap: starting traefik"

syslogd -n &
crond -f &
/entrypoint.sh "$@" & # traefik

# 'wait -n' not available in sh
# check if any jobs ended (!= 3), kill remaining jobs, wait and exit

while jobs > /dev/null && [ "$SIG" == "" ]; do # calling jobs (without -p) appears to be necessary to update the jobs
    JOBS=$(jobs -p)
    [ "$(echo "$JOBS" | wc -w)" == "3" ] || break
    sleep 1
done

echo "bootstrap: killing remaining jobs and waiting"
kill $(jobs -p)

# timeout of 10 * 0.5 seconds
TRIES=0
while jobs > /dev/null && [ "$(jobs -p)" != "" ] && [ "$TRIES" != "10" ]; do
    TRIES=$(($TRIES+1))
    sleep 0.5
done

if [ "$TRIES" != "10" ]; then
    echo "bootstrap: remaining jobs exited, bye"
else
    echo "bootstrap: not waiting any longer, bye"
fi

exit 0
