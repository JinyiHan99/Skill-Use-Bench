---
name: docker-patterns
description: Docker and Docker Compose patterns for local development, container security, networking, volume strategies, and multi-service orchestration.
origin: ECC
---

# Docker Patterns

Docker and Docker Compose best practices for containerized development.

## When to Activate

- Setting up Docker Compose for local development
- Designing multi-container architectures
- Troubleshooting container networking or volume issues
- Reviewing Dockerfiles for security and size
- Migrating from local dev to containerized workflow

## Dockerfile Best Practices

### Multi-Stage Builds with Named Stages

Every Dockerfile should use multi-stage builds. Name each stage with a descriptive `AS` alias following the convention `deps`, `dev`, `build`, `production` — this makes it easy to target specific stages from Compose and keeps the final image minimal.

```dockerfile
# Stage: dependencies
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage: dev (hot reload, debug tools)
FROM node:22-alpine AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# Stage: build
FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build && npm prune --production

# Stage: production (minimal image)
FROM node:22-alpine AS production
WORKDIR /app
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001
USER appuser
COPY --from=build --chown=appuser:appgroup /app/dist ./dist
COPY --from=build --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=build --chown=appuser:appgroup /app/package.json ./
ENV NODE_ENV=production
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/server.js"]
```

### Image Tag Pinning

Always pin base images to a specific version tag, including the OS variant — for example `node:22-alpine` or `python:3.12-slim-bookworm`. The `:latest` tag is forbidden in all Dockerfiles and Compose image references because it breaks reproducibility: a build that works today may silently break tomorrow when the upstream tag advances. Even in development Compose files, every `image:` field must carry an explicit version (e.g., `postgres:16-alpine`, `redis:7-alpine`).

### Non-Root Execution

The production stage must always create a dedicated application user and group, then switch to that user with `USER` before any `COPY` or `CMD`. Running containers as root is a common attack vector — a compromised process running as root has unrestricted access to the host kernel via volume mounts and capabilities. When creating the user, assign deterministic numeric IDs (UID/GID 1001 is the convention in this stack) so that file ownership is predictable across rebuilds.

### No Secrets in Image Layers

Sensitive values — API keys, database passwords, tokens — must never appear in `ENV`, `ARG`, `RUN echo`, or `COPY`'d config files baked into the image. Secrets embedded in image layers persist in the layer cache and can be extracted by anyone with access to the image. Instead, inject secrets at runtime through environment variables (`env_file` in Compose) or Docker Secrets in Swarm mode. If a Dockerfile or Compose file is found to contain a hardcoded secret value in an `ENV` or `environment` directive, it must be refactored to use `env_file` referencing a `.env` file (which itself must be listed in `.dockerignore` and `.gitignore`).

## Docker Compose for Local Development

### Service Dependencies with Health Checks

When one service depends on another (e.g., an app depending on a database), always use the long-form `depends_on` with `condition: service_healthy` and provide a proper `healthcheck` on the dependency. A bare `depends_on: [db]` only waits for the container to start, not for the service inside to be ready — this causes race conditions where the app tries to connect before the database accepts connections.

```yaml
services:
  app:
    build:
      context: .
      target: dev
    ports:
      - "3000:3000"
    volumes:
      - .:/app
      - /app/node_modules
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: npm run dev

  db:
    image: postgres:16-alpine
    ports:
      - "127.0.0.1:5432:5432"
    env_file:
      - .env
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "127.0.0.1:6379:6379"  # Bind to localhost only; never expose cache to 0.0.0.0
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

### Override Files for Environment Separation

Use `docker-compose.override.yml` for development-only settings (debug ports, verbose logging, hot-reload volumes). This file is auto-loaded by `docker compose up` and should never be committed to the production deployment path. Production settings go in a separate `docker-compose.prod.yml` and are loaded explicitly:

```bash
# Development (auto-loads override)
docker compose up

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Networking

### Network Segmentation for Security

For multi-tier applications, define separate named networks for each trust boundary rather than relying on the default network. The database should only be reachable from the API layer, never directly from the frontend. This limits the blast radius if any single container is compromised.

```yaml
services:
  frontend:
    networks:
      - frontend-net

  api:
    networks:
      - frontend-net
      - backend-net

  db:
    networks:
      - backend-net

networks:
  frontend-net:
  backend-net:
```

### Host-Only Port Binding for Databases

Database and cache services in development should bind to `127.0.0.1` rather than `0.0.0.0` to prevent accidental exposure to the local network. In production Compose files, database ports should be omitted entirely — services communicate over the Docker network without exposing ports to the host.

```yaml
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"
```

## Volume Strategies

### Protecting Container-Generated Directories

When using bind mounts for hot reload (e.g., `.:/app`), package manager directories like `node_modules` or `.next` get overwritten by the host's (possibly empty) version. Always add anonymous volume mounts for these paths to preserve the container's copies:

```yaml
services:
  app:
    volumes:
      - .:/app
      - /app/node_modules
      - /app/.next
```

### Named Volumes for Persistent Data

All stateful data (database files, cache directories) must use named volumes — not bind mounts and not anonymous volumes. Named volumes survive `docker compose down` (though not `docker compose down -v`) and are managed by Docker's storage driver, ensuring consistent permissions and better I/O performance than bind mounts.

## Container Security in Compose

### Security Hardening Directives

Production services should include security hardening directives: `security_opt: [no-new-privileges:true]`, `cap_drop: [ALL]` (adding back only specifically needed capabilities), and `read_only: true` with explicit `tmpfs` mounts for directories that need write access. These directives limit what a compromised container can do.

```yaml
services:
  app:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /app/.cache
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

## .dockerignore

Every project with a Dockerfile must include a `.dockerignore` that excludes at minimum: `node_modules`, `.git`, `.env`, `.env.*`, `dist`, `coverage`, `*.log`, `.next`, `.cache`, `docker-compose*.yml`, `Dockerfile*`, `README.md`, and `tests/`. A missing or incomplete `.dockerignore` bloats the build context and risks leaking secrets into the image.

## Debugging

### Common Commands

```bash
# View logs
docker compose logs -f app
docker compose logs --tail=50 db

# Shell access
docker compose exec app sh
docker compose exec db psql -U postgres

# Inspect
docker compose ps
docker compose top
docker stats

# Rebuild
docker compose up --build
docker compose build --no-cache app

# Clean up
docker compose down
docker compose down -v
docker system prune
```

### Debugging Network Issues

```bash
docker compose exec app nslookup db
docker compose exec app wget -qO- http://api:3000/health
docker network ls
docker network inspect <project>_default
```

## Anti-Patterns

- Using Docker Compose in production without orchestration — use Kubernetes, ECS, or Docker Swarm for production multi-container workloads
- Storing data in containers without volumes — containers are ephemeral, all data is lost on restart
- Running containers as root — always create and use a non-root user
- Using the `:latest` tag — pin to specific versions for reproducible builds
- Packing all services into one giant container — one process per container
- Putting secrets in `docker-compose.yml` or Dockerfile `ENV` — use `.env` files (gitignored) or Docker secrets
- Relying on bare `depends_on` without health checks — leads to race conditions at startup
