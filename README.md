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

### Declare services (websites with git repositories)

Create the service configuration file 'services/some-service.conf':

    REPO_HOST="git@github.com:goncalomb"
    REPO_NAME="some-service"
    HOST="example.com"

It will build the container using the `Dockerfile` from the repository or `services/some-service.dockerfile`.

### Declare other services

Add them to `docker-compose.yaml`.

### Change traefik configuration

Edit `traefik/traefik.toml` and `traefik/traefik-dynamic.toml`.

## Start

To build the services and start everything:

    ./up-build.sh

## License

MIT, goncalomb
