# Containerize Service — Dockerfile + Kubernetes Manifests

## Purpose

This transformation containerizes a legacy web service so it can run on a
modern container platform (Docker + Kubernetes). It is the auto-remediation
paired with the Modernization Readiness (MODA) finding:

> "Service is not containerized — deployed directly to a host via a process
> manager (e.g. `forever`, systemd, manual SSH). No Dockerfile, no
> orchestration manifests. Blocks migration to ECS/EKS and horizontal scaling."

The transformation is **additive and non-destructive**: it generates new
container artifacts. It does NOT modify application source code, upgrade
dependencies, or change runtime behavior. The goal is to produce a reviewable
pull request that gives the team a working container baseline to iterate on.

## Scope

Generate exactly these artifacts at the repository root (create only the ones
that do not already exist; never overwrite an existing file):

1. `Dockerfile`
2. `.dockerignore`
3. `k8s/deployment.yaml`
4. `k8s/service.yaml`

Do **not** modify, delete, or reformat any other file in the repository.

## How to analyze the repository

Before generating anything, detect the service's runtime and shape:

1. **Language / runtime** — inspect manifests and entrypoints:
   - Node.js: `package.json` (read `engines.node`, `main`, `scripts.start`,
     `dependencies`). If `engines.node` pins an EOL version (e.g. `0.10.x`),
     pin the image to the **nearest supported LTS** (currently `node:20-alpine`)
     and note the upgrade in the PR body — do NOT attempt the code upgrade here.
   - Ruby: `Gemfile` / `config.ru` / Rails `config/` → use `ruby:<version>-slim`;
     honor `.ruby-version` if present, else nearest supported stable.
   - Java: `pom.xml` / `build.gradle` / `WEB-INF/` → build with a JDK image,
     run on a JRE image (multi-stage). Prefer `eclipse-temurin:<LTS>-jre`.
2. **Listen port** — search source for the bound port (e.g. `app.listen(PORT)`,
   `server.port`, `Rails` default `3000`, servlet container `8080`). If it
   cannot be determined, default to `8080` and record the assumption in the PR.
3. **Start command** — derive from `scripts.start`, `config.ru`, the WAR entry,
   or the documented run command. Strip any host-process-manager wrapper
   (`forever start X` → `node X`; `bundle exec ...` stays).
4. **Health endpoint** — if the code exposes `/health`, `/healthz`, `/status`,
   or `/ping`, wire the K8s probes to it. Otherwise use a TCP socket probe on
   the listen port and note that a dedicated health endpoint is recommended.
5. **Externalized config** — any hardcoded host/port/URL/secret (DB URLs, API
   keys) should be surfaced as container env vars in the manifests with
   placeholder values, and called out in the PR body as follow-up hardening.
   Do NOT invent real secret values; use `CHANGME`/env references.

## Dockerfile requirements

- Use a specific, currently-supported base image tag (never `latest`).
- Prefer a **multi-stage build** for compiled runtimes (Java) to keep the final
  image small; single-stage is fine for interpreted runtimes (Node, Ruby).
- Run as a **non-root user**. Create/adopt an unprivileged user and `USER` it.
- Set `WORKDIR /app`, copy dependency manifests first, install deps, then copy
  source — so layer caching works.
- `EXPOSE` the detected listen port.
- Use a JSON-array `CMD` (exec form), not shell form.
- Do NOT run the legacy host process manager (`forever`, `pm2`) inside the
  container — the container runtime IS the supervisor.
- Add a `HEALTHCHECK` only if a real health endpoint exists.

## .dockerignore requirements

Exclude at minimum: `.git`, `node_modules`, `vendor/bundle`, `log`, `tmp`,
`*.log`, build output dirs, and any local env files (`.env`). Tailor to the
detected runtime.

## Kubernetes manifest requirements

`k8s/deployment.yaml`:
- `apiVersion: apps/v1`, `kind: Deployment`.
- `metadata.name` and all labels use the service name (kebab-case, derived from
  the repo/package name).
- Standard label set: `app.kubernetes.io/name`, `app.kubernetes.io/part-of`.
- `replicas: 2` (the legacy single-instance deploy is a documented gap; two
  replicas demonstrate the horizontal-scaling win).
- One container referencing the image `<service-name>:latest` with a comment
  noting the image should be replaced by the registry-pushed tag.
- `containerPort` = detected listen port.
- `resources.requests` and `resources.limits` for cpu and memory (modest,
  clearly-labeled starter values).
- `readinessProbe` and `livenessProbe` (HTTP if a health endpoint exists, else
  TCP on the listen port).
- Any externalized config from the analysis surfaced as `env:` entries with
  placeholder values (never real secrets).
- `securityContext`: `runAsNonRoot: true`, drop all capabilities.

`k8s/service.yaml`:
- `apiVersion: v1`, `kind: Service`, `type: ClusterIP`.
- Selector matches the deployment labels.
- `port` 80 → `targetPort` = detected listen port (or expose the listen port
  directly if that reads cleaner for the runtime).

## Pull request

Against a GitHub/GitLab/Bitbucket source the changes land on a new branch and
open a PR. Against a **local** source (`--local`) there is no PR — the changes
are committed to a local staging branch and reviewed with `git diff main`. Write
the same content either way: as the PR/MR body when one is opened, and as the
commit message body when it is not. It MUST include:

- **What changed**: the four files added (name any that were skipped because
  they already existed).
- **Detected runtime**: language, version found vs. version pinned in the image
  (flag any EOL→LTS jump as a follow-up, not something this change performed).
- **Assumptions**: listen port, start command, health probe strategy.
- **Follow-up hardening**: externalized secrets to move into a real Secret/
  ConfigMap, dependency upgrades, adding a health endpoint if missing.
- A one-line note that this is a **container baseline** for the team to review,
  not a production-ready manifest.

## Guardrails

- NEVER overwrite an existing `Dockerfile`, `.dockerignore`, or `k8s/*` file —
  if present, skip that file and say so in the PR/commit body.
- NEVER modify application source, dependency manifests, or lockfiles.
- NEVER embed real credentials; use placeholders.
- Keep the change set to the four artifacts above. Small, reviewable, additive.
- If **every** target artifact already exists, make no change and say that
  plainly. Do not manufacture an unrelated edit to look productive — a no-op is
  the correct, honest outcome for an already-containerized repo.
