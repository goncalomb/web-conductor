# web-conductor

An opinionated system and configuration for Docker Compose to deploy services on a single server (e.g. VPS).

This project is now an Ansible role (2026). Ansible is required to prepare and deploy the system.

> [!NOTE]
> I use this to deploy many of my websites/services. This is MY opinionated setup, but it can be used as a base for ANY web-accessible services on a single server.
>
> A migration path for existing deployments should not be expected (e.g. files can be moved, vars can be renamed, etc.). If you update to a more recent version, check what changed, adjust any configuration, and, if necessary, completely redeploy the system from scratch. --goncalomb

## Features

- [Traefik](https://traefik.io/) router with custom configuration:
  - HTTP and HTTPS entry points (80 and 443);
  - Access and Traefik logs mounted on the host machine;
  - Log rotation;
  - Automatic discovery of Let's Encrypt certificates on the host machine (`/etc/letsencrypt`);
- [Grafana](https://grafana.com/oss/grafana/) provisioned with some default dashboards;
- [Loki](https://grafana.com/oss/loki/) preconfigured for log collection (container and access log);
- [Prometheus](https://grafana.com/oss/prometheus/) preconfigured for metrics collection;
- Default service (limbo) as a catch-all route (404);
- Declarative service configuration for multiple websites;

TODO:

- Built-in Certbot configuration;
- Markdown-based admin panel documentation;
- VPN for admin panel access (WireGuard);
- Tempo for tracing;
- Ansible tasks for backup;

## Requirements

- Testing: GNU/Linux or macOS with Ansible, Molecule and Docker;
- Deploying: GNU/Linux or macOS with Ansible;
- Target (e.g. VPS): Debian 13 (should work on any Debian-based distribution, but not tested);

## Testing / Demo

With Ansible, Molecule and Docker installed, start the test system by running:

```bash
molecule converge
```

This runs a preconfigured DinD (Docker-in-Docker) image and deploys the system. The main admin panel will be at <https://wc.localhost/>, a certificate error is expected (traefik self-signed), default password `admin:admin`. Ports 80 and 443 are hardcoded.

While running, inspect the system by connecting to the container:

```bash
molecule login
cd ~/web-conductor/
docker compose ps
```

To tear down the system, run:

```bash
molecule destroy
```

## Using

Use it as a normal Ansible role (not on Ansible Galaxy, use git):

`requirements.yml`

```yaml
roles:
  - name: goncalomb.web-conductor
    src: git+https://github.com/goncalomb/web-conductor.git
```

`playbook.yml`

```yaml
- name: Example playbook
  hosts: all
  tasks:
    - name: Run web-conductor
      ansible.builtin.include_role:
        name: goncalomb.web-conductor
      vars:
        wc_traefik_admin_host: admin.localhost
```

Running the role (main tasks) will prepare the entire system and start the services.

## Configuration

The system is primarily configured using Ansible vars, see [defaults/main.yml](defaults/main.yml).

For deploying user services, place extra `compose.XXX.yml` files in a `user/` directory (see the `wc_user_dir` var). This user directory will be synced with the host, and the compose files will ultimately be included as part of a final `compose.yml` in a single stack.

_The services may have a special `x-web-conductor` field for extra configuration, but this is not finalized yet, and not documented here. You can see how it works on the built-in services ([files/](files/), `compose.XXX.yml`)._

## License

web-conductor is released under the terms of the MIT License. See [LICENSE.txt](LICENSE.txt) for details.
