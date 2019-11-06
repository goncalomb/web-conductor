FROM traefik:v2.0

RUN apk --no-cache add logrotate

ADD traefik.toml /etc/traefik/traefik.toml
ADD traefik-dynamic.toml /etc/traefik/traefik-dynamic.orig.toml

ADD bootstrap.sh /

ADD logrotate.conf /etc/logrotate.d/traefik
RUN chmod 0644 /etc/logrotate.d/traefik

ENTRYPOINT ["/bootstrap.sh"]
CMD ["traefik"]
