# AWS Transform CLI Reference

Quick reference for the `atx` commands the orchestrator uses. Read this when you need to understand a flag, build an ATX configuration file, or look up an alternative invocation pattern.

> Full official reference: https://docs.aws.amazon.com/transform/latest/userguide/custom-command-reference.html

---

## Execute Transformation

```bash
atx custom def exec \
  -n <transformation-name> \
  -p <code-repository-path> \
  -g file://<configuration-file> \
  -x \
  -t
```

### Key Options

| Flag | Long form | Purpose |
|---|---|---|
| `-n` | `--transformation-name` | Name of the transformation definition (must match what's in the registry) |
| `-p` | `--code-repository-path` | Path to repository (`.` for current directory). Per-repo TDs use the repo path; portfolio TDs use `.` (workspace root). |
| `-g` | `--configuration` | Path to config file with `file://` prefix, or inline `key=value` pairs. Supports `additionalPlanContext` field for passing context to the transformation agent. |
| `-x` | `--non-interactive` | Run without user prompts. **Mandatory** for parallel/batch execution. |
| `-t` | `--trust-all-tools` | Trust all tools (no per-tool approval prompts). |
| `--tv` | `--transformation-version` | Pin to a specific TD version |

### Mandatory Flag Combination

For orchestrator-driven runs, always use **`-x -t`** together:

- `-x` (non-interactive) prevents the agent from blocking on prompts
- `-t` (trust-all-tools) prevents per-tool approval gates from blocking

Without these, subagent runs hang indefinitely waiting for user input.

### Always Use Absolute Paths

`-p` and `-g` arguments MUST be absolute paths in subagent flows. Each `executeBash` call starts a fresh shell — `cd` inside one call does not persist to the next call, so relative paths silently resolve against the workspace root rather than the intended directory. Symptoms range from ENOENT errors to artifacts landing at unexpected paths.

```bash
# ❌ Bad — relies on terminal CWD that may have drifted between calls:
atx custom def exec -n <td> -p . -g file://atx-config.yaml -x -t

# ✅ Good — absolute paths resolve identically regardless of CWD:
atx custom def exec -n <td> \
    -p /abs/path/to/repo \
    -g file:///abs/path/to/.atx-config.yaml \
    -x -t
```

**Pattern for subagents:** compute the absolute paths once in the same shell that issues the ATX command, then interpolate:

```bash
repo_abs=$(cd <repo_path> && pwd)
config_abs="$(pwd)/.atx-config-<slug>-<type>.yaml"
atx custom def exec -n <td> -p "$repo_abs" -g "file://$config_abs" -x -t
```

**Pattern for the orchestrator:** when generating per-repo ATX configs, emit absolute paths for both `-p` and `-g` in the per-repo subagent prompts. The workspace root path is known at orchestration time and absolute paths can be constructed deterministically. See troubleshooting.md ("ATX Fails with No such file or Wrong Working Directory") for the full failure-mode rationale.

---

## Configuration File Format

The `-g` flag accepts an ATX execution configuration file (YAML or JSON), **not arbitrary data**. To pass portfolio or service context to the transformation, use the `additionalPlanContext` field:

```yaml
# atx-config-ara.yaml — ARA per-repo (NO preferences)
additionalPlanContext: |
  repo_type: "application"
  service_archetype: "stateful-crud"
  agent_scope: "write-enabled"
  context: "Legacy Java monolith running on EC2"
  priority: "P0"
  tags: ["monolith", "java"]
```

```yaml
# atx-config-mod.yaml — MOD per-repo (NO agent_scope)
additionalPlanContext: |
  repo_type: "application"
  context: "Legacy Java monolith running on EC2"
  preferences:
    prefer: ["eks", "fargate"]
    avoid: ["serverless"]
  priority: "P0"
  tags: ["monolith", "java"]
```

The `additionalPlanContext` value is a multi-line string — embed YAML inside YAML using the `|` block scalar.

---

## List Available Transformations

```bash
atx custom def list
atx custom def list --json
```

Use `grep` to filter by name:

```bash
atx custom def list | grep agentic
atx custom def list | grep portfolio
```

---

## Get Transformation Details

```bash
atx custom def get -n <transformation-name>
atx custom def get -n <transformation-name> --tv <version>
```

Returns the TD's metadata, including the latest published version ID. Useful for verifying a specific version is what's running.

---

## Publish a Transformation

```bash
atx custom def publish \
  -n <transformation-name> \
  --sd <source-directory> \
  --description "<description>"
```

| Flag | Purpose |
|---|---|
| `-n` | TD name (becomes the registry identifier) |
| `--sd, --source-directory` | Local directory containing the TD's source files (typically `transformation_definition.md` and any referenced files) |
| `--description` | Short description shown in `atx custom def list` |
| `--tv, --transformation-version` | Pin to a specific version (cannot be combined with `--description` or `--source-directory`) |

> **⚠ Cannot run in parallel.** The atx CLI uses a shared tar staging path (`~/tmp/transformation.tar`). Concurrent publishes overwrite each other and produce ENOENT or 400 upload errors. Always publish serially.

---

## Interactive Mode (No Orchestrator)

```bash
atx                           # Start a new conversation
atx --resume                  # Resume the most recent conversation
atx -t                        # Start with all tools trusted
```

Useful for debugging when an automated run fails — interactive mode shows the agent's reasoning and lets you respond to prompts.

---

## Common Invocation Patterns

### Per-repo ARA

```bash
atx custom def exec -n <ara_td> -p ./services/checkout -g file://atx-config-checkout-ara.yaml -x -t
```

### Per-repo MOD

```bash
atx custom def exec -n <mod_td> -p ./services/checkout -g file://atx-config-checkout-mod.yaml -x -t
```

### Portfolio ARA

```bash
atx custom def exec -n <portfolio_ara_td> -p . -g file://atx-config-portfolio-ara.yaml -x -t
```

### Portfolio MOD

```bash
atx custom def exec -n <portfolio_mod_td> -p . -g file://atx-config-portfolio-mod.yaml -x -t
```

---

## Recommended `executeBash` Timeouts

| TD type | timeout (ms) | Wall clock |
|---|---|---|
| Per-repo ARA / MOD | 1200000 | 20 minutes |
| Portfolio ARA / MOD | 1800000 | 30 minutes |
| Very large repo (>1M LOC) | 2400000 | 40 minutes |

The macOS `timeout` shell command is not available — use the `executeBash` tool's `timeout` parameter directly.

---

## Related Resources

- [AWS Transform Documentation](https://docs.aws.amazon.com/transform/)
- [AWS Transform CLI Reference](https://docs.aws.amazon.com/transform/latest/userguide/custom-command-reference.html)
- [AWS Modernization Pathways (Skill Builder)](https://skillbuilder.aws/learning-plan)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
