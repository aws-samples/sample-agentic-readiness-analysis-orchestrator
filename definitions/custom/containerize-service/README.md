# `containerize-service` — the demo's remediation TD

Generates a container baseline (`Dockerfile`, `.dockerignore`, `k8s/deployment.yaml`,
`k8s/service.yaml`) for a service that has none. Additive and non-destructive: it never touches
application source, dependency manifests, or lockfiles, and it never overwrites an existing
artifact.

This is the TD the demo harness publishes and runs, so a full demo needs no hand-authoring. It
pairs with the MODA "service is not containerized" finding (`INF-Q1`).

## Why this exists as a repo file

TD names resolve against a **published registry** at run time, and registry state is not
version-controlled: drafts expire after ~30 days, TDs can be deleted, and the registry is shared
across everyone using the account. A TD that worked last month can vanish.

Keeping the source here means the demo can always re-publish what it needs instead of depending on
a name someone else has to have already created.

## Publish it

Publishing a TD to the registry is done with the internal publishing tooling, which is
maintained separately. The TD name comes from the folder basename, so **renaming the folder renames
the TD**.

## Run it

**Documented path** — remediation's *direct-TD* mode. Needs no findings (it runs a transformation
against a repository directly), is visible in the Console's **Remediations** tab, and produces a
branch/PR (`--local` → a local branch):

```bash
atx ct remediation create --repo <src>::<repo> --source <src> \
  --transformation-name containerize-service --name "containerize" --local
atx ct remediation status --id <remediation-id>
```

**The TD must be published before `ct remediation` can reference it by name** (see "Publish it"
above). The registry is scoped by authentication mode, and the `ct remediation` worker reads only
one of them — a TD published the other way is a 404 there even though `custom def get` confirms it.

**Local fallback** — same TD, no registry round-trip, changes left uncommitted:

```bash
AWS_REGION=us-east-1 atx custom def exec -n containerize-service -p <abs-repo-path> -x -t
git -C <abs-repo-path> status --short   # see what it generated
```

Two preconditions that bite in practice:

- **The worktree must be clean** if you route through `ct remediation` — a repo that was just
  analyzed is dirty (`ct` writes its report bundle into the working tree) and remediation refuses
  with *"has uncommitted changes."* `custom def exec` runs against a dirty tree, but a clean start
  makes the generated-files diff obvious.
- **Pick a repo that actually lacks a Dockerfile.** In `harness/fixtures/portfolio`,
  `legacy-loan-calculator` (Java/Struts) and `legacy-storefront-rails` (Rails) have none.
  `legacy-shipping-api` and `legacy-pricing-cgi` ship a `Dockerfile` and `k8s/` already, so this
  TD correctly does almost nothing on them — a real but unimpressive result.

## Verify it resolves before demoing

```bash
cd "$(mktemp -d)" && AWS_REGION=us-east-1 atx custom def get -n containerize-service
#   "✓ ... retrieved successfully"  -> ready
#   "Error: ... not found."         -> re-publish (see above)
```

Run this in the same authentication mode the remediation worker uses — a pass in the other mode says
nothing about whether remediation can resolve the name.

Prefer `get -n <name>` over grepping `atx custom def list`: the list is long, wraps names across
lines, and its managed/user split is a section header rather than a per-row field.

## Schema

`DEFAULT` schema (`transformation_definition.md` + optional `summaries.md`), detected automatically
by the publisher. The other TDs in this repo use the `EXPERIMENTAL_SKILL` schema
(`SKILL.md` + `references/`); both are valid, and the publisher picks the right one from which file it finds.
