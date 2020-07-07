# web-conductor

An opinionated configuration for docker-compose to deploy services on a single server.

This project was created to help build and deploy multiple containerized websites (different hosts) on a single server.

**This is a work in progress with few features and documentation. Anything can change!**

Features:

* [traefik](https://traefik.io/) router with custom configuration:
  - http and https entry points (80 and 443)
  - dashboard on port 81 (https)
  - access and traefik logs mounted on the host machine
  - log rotation
  - automatic discovery of Let's Encrypt certificates on the host machine (`/etc/letsencrypt`)
* default service (limbo) as a catch all route (404)
* declarative service configuration for multiple websites

**This is meant to be installed directly server that will run the containers (usage with Docker Swarm is untested).**

## Installation

Install 'docker' and 'docker-compose'. Clone this repository.

## Configuration

### Declare Services

Services are declared on `docker-compose-XXX.yaml` files. These can be normal docker-compose services or with some extras...

The services can have an extra 'web-conductor' property with some configurations:

    version: "3.7"

    services:
      some-website:
        web-conductor:
          repo-host: git@github.com:goncalomb
          repo-name: some-website
          host: example.com
          https-redirect: True (defaults to True)

These extra configurations will be used to build the services and create `traefik` labels.

For this to work you need to use `web-conductor.py` to interact with docker...

Create as many `docker-compose-XXX.yaml` files as you want (e.g. docker-compose-001.yaml, docker-compose-002.yaml).

### Using

To interact with the services use `web-conductor.py`, this script "compiles" all the `docker-compose-XXX.yaml` files before calling `docker-compose`.

    usage: web-conductor [-h] [--sudo] {compose,volume,bash,up,down} ...

* `./web-conductor.py up` - alias for `compose up -d --remove-orphans`
* `./web-conductor.py down` - alias for `compose down --remove-orphans`
* `./web-conductor.py compose` - call docker-compose
* `./web-conductor.py bash` - dump service data for bash processing (internal use)
* `./web-conductor.py volume backup` - backup named volume

#### Fetch (WIP)

Use `./fetch.sh` to clone and build all services declared using the special `web-conductor` configuration... This will eventually be included in `web-conductor.py`.

### Change traefik configuration

Edit `traefik/traefik.toml` and `traefik/traefik-dynamic.toml`.

## License

MIT, goncalomb
