#!/bin/sh

set -e

echo "bootstrap: hi"

LETSENCRYPT_DIR=/etc/letsencrypt/live
CONF_FILE=/etc/traefik/dynamic/certificates.toml
search_certificates() {
    : >"$CONF_FILE"
    if [ ! -d "$LETSENCRYPT_DIR" ]; then
        echo "bootstrap: '$LETSENCRYPT_DIR' not found, skipping certificate search"
        return
    fi
    echo "bootstrap: searching '$LETSENCRYPT_DIR' for tls certificates"
    for FOLDER in "$LETSENCRYPT_DIR"/*; do
        [ -d "$FOLDER" ] || continue
        CERT_FILE="$FOLDER/fullchain.pem"
        KEY_FILE="$FOLDER/privkey.pem"
        if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
            echo "bootstrap: found tls certificate '$FOLDER'"
            {
                echo "[[tls.certificates]]"
                echo "    certFile = \"$CERT_FILE\""
                echo "    keyFile = \"$KEY_FILE\""
            } >>"$CONF_FILE"
        else
            echo "bootstrap: missing files in '$FOLDER', skipping"
        fi
    done
}

TRAEFIK_PID=
signal_usr1() {
    echo "bootstrap: received USR1, sending to traefik"
    [ -n "$TRAEFIK_PID" ] && kill -USR1 "$TRAEFIK_PID"
}

signal_usr2() {
    echo "bootstrap: received USR2, reloading certificates"
    search_certificates
}

KILL=
signal_kill() {
    echo "bootstrap: received kill signal"
    KILL=1
}

trap signal_usr1 USR1
trap signal_usr2 USR2
trap signal_kill INT TERM

# initial certificate search

search_certificates

# in addition to traefik, we need syslogd and crond for log rotation
# start everything as background jobs and wait for any to finish

echo "bootstrap: starting traefik"

syslogd -n &
crond -f &
/entrypoint.sh "$@" & # traefik
TRAEFIK_PID=$!

# 'wait -n' not available in sh
# check if any jobs ended (!= 3), kill remaining jobs, wait and exit

while jobs > /dev/null && [ -z "$KILL" ]; do # calling jobs (without -p) appears to be necessary to update the jobs
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
