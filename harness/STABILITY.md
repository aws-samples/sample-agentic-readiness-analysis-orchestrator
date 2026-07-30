# Scoring Stability — how much of an accuracy number is real?

The harness exists to answer one question about a proposed TD change: **did this make the
analysis better?** That question is only answerable if we know how much a score moves when
*nothing* changes. This document records that noise floor, so a future claim of improvement
can be checked against it.

The short version: **on ARA, run-to-run noise reaches 0.10 per fixture on byte-identical
inputs. On MOD it is 0.00.** Any ARA improvement smaller than ~0.10 on a single fixture, or
~0.04 on the 11-fixture mean, has not been measured — it has been observed once.

## What varies, and what does not

Three layers sit between a TD edit and a number, and they are not equally stable:

| Layer | Varies? | Why |
|---|---|---|
| The TD prompt (`SKILL.md`) | No | It is a file. It changes only when someone edits it. |
| The **analysis agent** that applies it | **Yes, a lot** | An LLM agent walking a repo. A re-run against the same fixture and the same rubric moves 10–20 findings. |
| The **scorer** (`score-reports.py`) | Yes, mildly | Also an LLM, though its input is a small JSON report rather than a repo. |

The middle row is the dominant term, and it is the one that matters: **what we are measuring
is TD output quality**, so a sample must be one *run of the TD*, not one *pass of the scorer
over a saved report*. Re-scoring the same report N times holds constant the very thing that
varies and reports a false precision.

That is why `--trees` takes N report trees rather than `--runs` taking N scorer passes:

```sh
# Produce independent samples (each is a full analysis run — the expensive part).
harness/run-fixtures.sh --scope all --after-dir harness/_run1
harness/run-fixtures.sh --scope all --after-dir harness/_run2
harness/run-fixtures.sh --scope all --after-dir harness/_run3

# Score them as samples of the same TD. Each row gets mean / stddev / spread.
harness/score-reports.py --trees harness/_run1 harness/_run2 harness/_run3
```

Cost is the binding constraint: each unit bills ~110–130 agent-minutes, so a 3-sample sweep
over 11 fixtures × 2 analyses is ~66 units. This is a deliberate, occasional measurement —
not something an MR runs.

## Measurement: two independent scorer passes, identical inputs

Both passes scored the **same committed `harness/golden/` tree** with the same rubric. The
only difference between them was a refactor that moved the severity table from a hardcoded
string to a `SKILL.md` parse — verified content-neutral, so every delta below is noise.

| | ARA | MOD |
|---|---|---|
| Fixtures that moved | **6 of 11** | **0 of 11** |
| Worst single move | **0.10** | 0.00 |
| Mean absolute move | 0.038 | 0.000 |
| Mean score, pass 1 → pass 2 | 0.700 → 0.727 | 0.913 → 0.913 |

Per-fixture ARA deltas: `document-portal +0.10`, `loan-calculator +0.10`, `payroll +0.06`,
`timesheet-webforms +0.06`, `helpdesk-tickets −0.06`, `shipping-api +0.04`; unchanged on
`crm-desktop`, `partner-soap`, `pricing-cgi`, `storefront-rails`, `monolith`.

### Why ARA is noisy and MOD is not

MOD's scores cluster tightly at the floor (0.88–0.92, all 11 fixtures on legacy code with
`overall_score` 1.15–1.89). Every fixture is unambiguously "Not Ready", so there is nothing
for the scorer to be uncertain about — the answer is overdetermined.

ARA's scores span 0.42–0.92. That range is where judgement lives: severity calls,
evidence-quality assessments, and how many findings a given re-run happened to surface. A
wider distribution is not a defect in ARA — it reflects genuinely harder calls — but it does
mean ARA needs more samples to say anything.

**This asymmetry has a direct consequence:** the ARA-vs-MOD gap (0.73 vs 0.91) is *larger*
than the noise and is real. But it is partly a property of the fixture set, not only of the
TDs. Every fixture is floor-scoring legacy code, which flatters MOD and stresses ARA. See
"fixture spread" below.

## Rules of thumb

1. **Single-fixture ARA deltas below 0.10 are not evidence.** Neither are 11-fixture ARA
   mean deltas below ~0.04.
2. **A MOD delta of any size is worth a look**, because MOD's floor is stable — but only
   until fixtures exist that score above the floor, at which point re-measure.
3. **Report the spread alongside the mean, always.** A mean with no spread invites the
   reader to over-trust it. `--trees` prints `sd` and `spread` columns for this reason.
4. **Deterministic checks are exempt.** The pre-checks (`--checks-only`) are arithmetic:
   severity counters, tier derivation, `overall_score` vs its category mean, 43/37 coverage.
   They return the same answer every time, which is precisely why anything expressible as
   arithmetic belongs there and not in the LLM's lap.

## Known confound: the fixture set has no spread

Every current fixture is floor-scoring legacy code. Consequences:

- ARA severity and MOD maturity are **perfectly correlated** across all 11 fixtures, so the
  two analyses cannot be distinguished by their results.
- The `blocker_count == 0` half of the ARA tier arithmetic **has never run on a real
  fixture**. `risk_safety_count` has never once driven a tier.
- No fixture reaches Pilot-Ready, Pilot-Ready (Safety Concerns), Agent-Ready, or MOD
  Partial/Mature.

A latent rubric bug was found precisely here: the benchmark prompt's "Safety Concerns"
qualifier rule was factually wrong, but it could only misfire at `blocker_count == 0` — a
state no fixture reaches — so it would have first surfaced as a mystery failure on the first
Pilot-Ready fixture ever added. Fixtures that exercise the upper tiers are tracked
separately and are a prerequisite for trusting scores in that half of the range.

## Caveat on the numbers above

Two passes give a range, not a standard deviation worth quoting. The 0.10 figure is a
*floor* on ARA's noise, not a characterization of its distribution — with n=2 the true worst
case is very likely larger. Treat it as "at least this much" until a 3+ sample sweep runs.
