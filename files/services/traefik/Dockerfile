FROM traefik:v3

RUN apk --no-cache add logrotate

ADD traefik.toml /etc/traefik/traefik.toml
ADD dynamic /etc/traefik/dynamic

ADD bootstrap.sh /

ADD logrotate.conf /etc/logrotate.d/traefik
RUN chmod 0644 /etc/logrotate.d/traefik

ENTRYPOINT ["/bootstrap.sh"]
CMD ["traefik"]
