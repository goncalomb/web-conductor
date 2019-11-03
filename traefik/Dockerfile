FROM traefik:v2.0

RUN apk update && apk add logrotate

ADD traefik.toml /etc/traefik/traefik.toml
ADD traefik-dynamic.toml /etc/traefik/traefik-dynamic.toml
ADD entrypoint-bootstrap.sh /
ADD logrotate.conf /etc/logrotate.d/traefik
RUN chmod 0644 /etc/logrotate.d/traefik

ENTRYPOINT ["/entrypoint-bootstrap.sh"]
CMD ["traefik"]
