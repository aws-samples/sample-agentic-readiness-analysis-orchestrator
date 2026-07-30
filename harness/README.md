# Change-Impact Harness — Operator Guide

The harness gives contributors automatic, advisory feedback on any change to one of
the four **managed** AWS Transform TDs (`agentic-readiness-analysis`,
`modernization-readiness-analysis`, `portfolio-agentic-readiness-analysis`,
`portfolio-modernization-readiness-analysis`). On each merge request it re-runs the
changed TD over a representative set of fixtures, computes a deterministic D1–D5
delta versus committed golden baselines, and has an LLM-as-judge score **whether that
delta makes the analysis better or worse** — posting the verdict as an MR comment. It
never blocks a merge. For the full design (dimensions, differ contract, trigger
model), see [`DESIGN.md`](./DESIGN.md).

The judge's 0–100 score answers one question: **does this change make the ARA/MOD
assessment more accurate, more useful, and safer to act on?** (85+ clear improvement ·
45–59 neutral · under 45 likely degradation). A no-op is *neutral*, so it lands
mid-band — the bottom of the range is reserved for real damage to the assessment. The
contributor's stated intent is reported as supporting evidence and shapes confidence,
but does **not** drive the score: a change can be described perfectly and still degrade
the analysis. See [`DESIGN.md` §6.1](./DESIGN.md) for the calibration ladder.

> **Automation is GitLab-only.** All CI runs on `gitlab.aws.dev`, where AWS access
> is granted via the **AWS Credential Vendor** (see below). GitHub stays open for
> issues and PRs but runs no automation.

## Set up AWS access (AWS Credential Vendor — no long-lived credentials)

The `atx` (AWS Transform) step needs AWS access on the GitLab runner.

> **Why not OIDC?** On the *public* GitLab, the usual pattern is an IAM OIDC
> provider that trusts the instance. That does **not** work on the internal
> `gitlab.aws.dev`: AWS IAM cannot reach the private instance to verify the
> `id_token`, so OIDC is not an option here.
> ([ref](https://w.amazon.com/bin/view/Users/dnchi/AWSGitLab/))

Instead we use the **AWS Credential Vendor**, which is built into the **shared
runner fleet**. The runners' jump role
`arn:aws:iam::979517299116:role/gitlab-runners-prod` assumes a role **you** create
in your Isengard account, gated by GitLab principal tags. The runner then injects
temporary `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` into
the job automatically — there is nothing to exchange in `before_script`, and no
static keys are stored. Two constraints:

- It **only works on shared runners** (already enabled here — the CI pins
  `tags: [shared]`).
- The role is **per-project** — it cannot be reused across GitLab projects.

### 1. Create the IAM role in your Isengard account

Create a role whose **trust policy** lets the shared-runner jump role assume it,
scoped to *this* GitLab group + project via principal tags. Replace `<GROUP>` and
`<PROJECT>` with this project's path segments — for
`gitlab.aws.dev/agentic-readiness-assessment/agentic-readiness-assessment` that is
group `agentic-readiness-assessment`, project `agentic-readiness-assessment`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::979517299116:role/gitlab-runners-prod"
      },
      "Action": [
        "sts:AssumeRole",
        "sts:TagSession"
      ],
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/GitLab:Project": "<PROJECT>",
          "aws:PrincipalTag/GitLab:Group": "<GROUP>"
        }
      }
    }
  ]
}
```

One-liner to create it (run with your Isengard admin credentials; save the trust
policy above as `trust.json`):

```sh
aws iam create-role \
  --role-name ara-harness-gitlab-access \
  --description "GitLab shared runners -> ARA change-impact harness analysis access" \
  --assume-role-policy-document file://trust.json
```

### 2. Attach a least-privilege permissions policy

Give the role **only** the AWS actions the analysis needs (the `atx` / AWS Transform
calls and supporting read access). Keep it **analysis-scoped, not admin** — no
write/delete on unrelated resources, no `AdministratorAccess`. Attach it with
`aws iam put-role-policy` (inline) or `attach-role-policy` (managed).

### 3. Add the GitLab CI variables

Click-path (GitLab project on `gitlab.aws.dev`): **Settings → CI/CD → Variables →
Add variable**.

| Variable | What it is | Masked | Protected |
|---|---|---|---|
| `AWS_CREDS_TARGET_ROLE` | ARN of the IAM role created in step 1 — the trigger the Credential Vendor keys off | No | Yes |
| `AWS_REGION` | Region for the analysis run (`us-east-1`) | No | Yes |

Notes:

- `AWS_CREDS_TARGET_ROLE` is the **only** switch — when it is set, the shared runner
  vends creds for it automatically; when it is unset, the job logs a clear warning
  and no AWS access is granted. An ARN and a region are not secret, so both are
  **protected but not masked** (masking rejects such values anyway). `AWS_REGION`
  defaults to `us-east-1` if unset.
- **No token to refresh.** The Vendor removes the old Isengard session-token expiry
  pain — no static keys to rotate; fresh short-lived credentials on every run.
- **Protect the branch.** For a *protected* variable to be injected, the running
  branch must be Protected. Mark `feat/harness` (and any release branches) Protected
  under **Settings → Repository → Protected branches**, or `AWS_CREDS_TARGET_ROLE`
  will be absent and no creds will be vended.
- **Multiple roles/stages?** If you later split analysis across accounts, each job
  can set its own `AWS_CREDS_TARGET_ROLE` value and the Vendor assumes accordingly.

## How it runs

Two advisory jobs, both `allow_failure: true` (they never block a merge). See
[`.gitlab-ci.yml`](../.gitlab-ci.yml).

- **`harness:contract-tests`** — offline schema guardrail (no AWS). Runs
  `tests/test_validate_contract.py` on every MR (and web run) to prove the JSON-contract
  validator still rejects drifted report shapes. This is the structural axis, distinct
  from the semantic judge; it needs no creds and no fixtures.
- **`harness:impact`** — runs automatically on every merge request. A deterministic
  gate (`should-run.sh`) decides run vs skip: it RUNs when a change lands under a
  watched TD directory (`definitions/managed/<td>/`, configurable via `HARNESS_TD_PATHS`)
  or a fixture; otherwise it skips. It publishes the edited TD as a custom def and runs
  it over the changed fixtures (`--changed-only --validate`), diffs against `golden/`,
  and the judge scores the delta's **effect on the analysis**, reading the **MR
  description** (per the TD-change MR template) as intent evidence. The verdict is
  posted as an MR comment.
- **`harness:full`** — manual only, via the **Run pipeline** button (web-triggered).
  Use it to force a full re-baseline (e.g. after publishing an approved change). Set
  `CHANGED_TD`, `RUN_SCOPE` (default `all`), and `RUN_INTENT` when launching. With no
  MR, it prints the verdict instead of commenting.

Both analyze jobs emit `impact.json` and `verdict.json` as artifacts.

## Local dev

You can exercise the differ without AWS or `atx` — it only reads report JSON:

```sh
# Diff two report trees (e.g. a hand-made "after" vs the committed goldens),
# using the committed golden baseline as input.
harness/diff-reports.py \
  --baseline harness/golden \
  --after harness/golden \
  -o /tmp/impact.json
# (Same tree in/out => an all-empty delta with "no_op": true — a good smoke test.)

# Run the differ unit tests (synthetic before/after pairs).
python -m pytest harness/tests/
```

`judge.py` is the only component that needs an LLM; the gate, differ, and coverage
heatmap (`coverage-heatmap.py`, rendered from `usecases.yaml` axes) all run offline.
