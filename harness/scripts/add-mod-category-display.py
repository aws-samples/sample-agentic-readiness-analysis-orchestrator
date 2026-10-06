#!/usr/bin/env python3
"""Add the additive `category_display` sibling field to every object that carries
a `category` field in the MOD golden reports (per-repo + portfolio).

Context: UI-parity row M1/M2. The CM Console renders the service's canonical
(LONG) category display label. Our MOD reports keep `category` as the stable
internal program-matching key (which the portfolio program-library matches on)
and now emit a sibling `category_display` = the console-canon LONG label, so the
console and our HTML/MD/JSON all agree. `category` is left EXACTLY as-is.

The map applies two LONG overrides to the SHORT forms the MOD
`04-output-contract.md` Category-Display table lists, and identity for the rest.
The dimension short codes and their labels are authoritative in
`harness/rubric/mod-scorer-prompt.md` (INF/APP/DATA/SEC/OPS):

    INF  Infrastructure & DevOps      -> Infrastructure, Platform, and DevOps   (override)
    APP  Application Architecture     -> Application Architecture               (identity)
    DATA Data Platform                -> Data Platform Modernization            (override)
    SEC  Security Baseline            -> Security Baseline                      (identity)
    OPS  Operations & Observability   -> Operations & Observability             (identity)

Design — TWO PASS (independent model re-review):

  Pass 1 — structural detection & validation (formatting-INDEPENDENT). The file
  is parsed with `json.loads` (using a duplicate-key-detecting hook) and the
  parsed object tree is walked recursively. For EVERY dict that carries a
  `category` key:
    * dimension value + already has `category_display`: ASSERT it equals the
      canonical value; a present-but-WRONG value is an ERROR (never overwritten).
    * dimension value + no `category_display`: recorded as a needed add.
    * a recognized non-dimension label: skipped (no add).
    * any other value: ERROR (unknown category), reported with json-path + file.
  Because it walks parsed structure — not lines — inline, comma-less,
  non-adjacent, wrong-value, and duplicate-key cases are ALL caught. This is the
  real "assert every object / reject every unknown" guarantee.

  Pass 2 — line-surgical insertion (only runs if Pass 1 found adds). The
  byte-preserving line insertion is applied, then the result is re-parsed
  (duplicate-key-detecting) and re-validated by Pass 1: the self-check ASSERTS
  the write produced exactly the intended structure (zero remaining adds, zero
  errors, no duplicate keys). A candidate that fails the self-check is REFUSED
  (raises) — a bad/partial file is never written.

On the already-correct goldens Pass 1 validates all `category_display` values,
finds zero adds and zero errors, so Pass 2 never runs -> byte-for-byte no-op ->
`git diff --stat harness/golden/` is empty. Same end state, real guarantee.

Deterministic (no engine run). Line insertion touches NO other formatting
(compact inline objects, `1.00`-style numbers, indent, trailing newline).

Run `--self-test` to exercise the guarantees on synthetic inputs.
"""
import glob
import json
import os
import re
import sys

# Authoritative MOD dimension mapping: short_code -> (category internal key, category_display console-canon label).
DIMENSIONS = {
    "INF": ("Infrastructure & DevOps", "Infrastructure, Platform, and DevOps"),
    "APP": ("Application Architecture", "Application Architecture"),
    "DATA": ("Data Platform", "Data Platform Modernization"),
    "SEC": ("Security Baseline", "Security Baseline"),
    "OPS": ("Operations & Observability", "Operations & Observability"),
}

# Explicit allowlist of dimension short codes (see harness/rubric/mod-scorer-prompt.md).
DIMENSION_SHORT_CODES = frozenset(DIMENSIONS)  # {"INF", "APP", "DATA", "SEC", "OPS"}

# category (internal string) -> category_display (console canon). Derived from DIMENSIONS.
CATEGORY_DISPLAY_MAP = {cat: disp for cat, disp in DIMENSIONS.values()}

# Allowlist of accepted `category` string values (the dimension internal keys).
DIMENSION_CATEGORY_VALUES = frozenset(CATEGORY_DISPLAY_MAP)

# `category` string values that are legitimately NOT modernization dimensions and
# must be skipped WITHOUT adding category_display. None exist in MOD today; every
# category-bearing object across all 16 goldens is one of the five dimensions. Add
# a value here only if the schema deliberately grows a non-dimension category.
KNOWN_NON_DIMENSION_LABELS = frozenset()

# Startup self-check: the map must cover exactly the five dimension short codes.
assert DIMENSION_SHORT_CODES == {"INF", "APP", "DATA", "SEC", "OPS"}, DIMENSION_SHORT_CODES
assert len(CATEGORY_DISPLAY_MAP) == 5, CATEGORY_DISPLAY_MAP

# Matches a `"category": "<value>",` line, capturing indent and the raw JSON value.
# Only the exact key "category" (never "category_id", "category_scores", ...).
# Used ONLY by Pass 2, whose correctness is guaranteed by the structural self-check.
CATEGORY_LINE = re.compile(r'^(?P<indent>\s*)"category":\s*"(?P<value>(?:[^"\\]|\\.)*)",\s*$')
# Matches a following `"category_display": "<value>",` line.
CATEGORY_DISPLAY_LINE = re.compile(r'^\s*"category_display":\s*"(?:[^"\\]|\\.)*"\s*,?\s*$')


class DuplicateKeyError(ValueError):
    """Raised when a JSON object contains a duplicate key (json.loads would
    otherwise silently keep last-wins, masking a bad Pass-2 insertion)."""


def _no_dup_pairs(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise DuplicateKeyError(f"duplicate key {k!r}")
        seen[k] = v
    return seen


def loads_strict(text):
    """json.loads that rejects duplicate keys anywhere in the document."""
    return json.loads(text, object_pairs_hook=_no_dup_pairs)


def new_counts():
    return {
        "n_added": 0,
        "n_already_had_display": 0,
        "n_skipped_non_dimension": 0,
        "n_errored": 0,
    }


def validate_tree(obj, jsonpath, file_label, counts, needs_add, errors):
    """PASS 1: recursively walk the PARSED object tree (formatting-independent).
    Populates counts, appends (jsonpath, value, expected) to needs_add for each
    dimension object missing category_display, and appends human messages to
    errors for unknown / present-but-wrong values. Never raises."""
    if isinstance(obj, dict):
        cat = obj.get("category")
        if isinstance(cat, str):
            cpath = f"{jsonpath}.category"
            if cat in DIMENSION_CATEGORY_VALUES:
                expected = CATEGORY_DISPLAY_MAP[cat]
                if "category_display" in obj:
                    existing = obj["category_display"]
                    if existing == expected:
                        counts["n_already_had_display"] += 1
                    else:
                        errors.append(
                            f"{file_label}: {cpath}: category={cat!r} has "
                            f"category_display={existing!r} but expected {expected!r}"
                        )
                        counts["n_errored"] += 1
                else:
                    needs_add.append((cpath, cat, expected))
            elif cat in KNOWN_NON_DIMENSION_LABELS:
                counts["n_skipped_non_dimension"] += 1
            else:
                errors.append(
                    f"{file_label}: {cpath}: unknown `category` value {cat!r} "
                    f"(not a MOD dimension {sorted(DIMENSION_CATEGORY_VALUES)} "
                    f"and not a known non-dimension label)"
                )
                counts["n_errored"] += 1
        for k, v in obj.items():
            validate_tree(v, f"{jsonpath}.{k}", file_label, counts, needs_add, errors)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            validate_tree(item, f"{jsonpath}[{idx}]", file_label, counts, needs_add, errors)


def insert_displays(text):
    """PASS 2 mechanism: byte-preserving line insertion. Adds a
    `category_display` line after each canonical `"category": "<dim>",` line that
    is not already followed by a category_display line. Correctness is enforced
    by the caller's structural self-check, not by this line scan. Returns
    (new_text, n_inserted)."""
    lines = text.split("\n")
    out = []
    n = len(lines)
    inserted = 0
    i = 0
    while i < n:
        line = lines[i]
        out.append(line)
        m = CATEGORY_LINE.match(line)
        if m:
            value = json.loads(f'"{m.group("value")}"')
            if value in DIMENSION_CATEGORY_VALUES:
                nxt = lines[i + 1] if i + 1 < n else ""
                if not CATEGORY_DISPLAY_LINE.match(nxt):
                    out.append(
                        f'{m.group("indent")}"category_display": '
                        f'{json.dumps(CATEGORY_DISPLAY_MAP[value])},'
                    )
                    inserted += 1
        i += 1
    return "\n".join(out), inserted


def process_text(text, file_label):
    """Two-pass processing of one document's text.

    Returns (new_text_or_None, counts, errors):
      * errors non-empty  -> new_text is None (nothing to write; caller reports).
      * no adds needed     -> new_text == text (byte-for-byte no-op).
      * adds performed     -> new_text is the migrated text (self-checked).
    Raises DuplicateKeyError on malformed input, or AssertionError if a Pass-2
    write fails its structural self-check (never emits a bad file)."""
    counts = new_counts()
    errors = []

    # PASS 1 — parse (dup-detecting) + structural validation.
    parsed = loads_strict(text)
    needs_add = []
    validate_tree(parsed, "$", file_label, counts, needs_add, errors)

    if errors:
        # Unknown or present-but-wrong values: refuse, do not write.
        return None, counts, errors

    if not needs_add:
        # Every dimension object already correct — verbatim no-op.
        return text, counts, errors

    # PASS 2 — line-surgical insertion, then structural self-check.
    new_text, n_inserted = insert_displays(text)

    recheck_counts = new_counts()
    recheck_needs = []
    recheck_errors = []
    reparsed = loads_strict(new_text)  # raises DuplicateKeyError if Pass 2 dup'd a key
    validate_tree(reparsed, "$", file_label, recheck_counts, recheck_needs, recheck_errors)

    if recheck_needs or recheck_errors:
        raise AssertionError(
            f"{file_label}: Pass-2 self-check failed — "
            f"remaining_adds={[p for p, _, _ in recheck_needs]} "
            f"errors={recheck_errors} (no file written)"
        )
    if n_inserted != len(needs_add):
        raise AssertionError(
            f"{file_label}: Pass-2 inserted {n_inserted} lines but Pass 1 "
            f"identified {len(needs_add)} adds (no file written)"
        )

    counts["n_added"] = len(needs_add)
    return new_text, counts, errors


def main(argv):
    if "--self-test" in argv:
        return run_self_test()

    golden_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "golden"
    )
    pattern = os.path.join(golden_dir, "*-mod-report.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"No MOD golden files matched {pattern}", file=sys.stderr)
        return 1

    totals = new_counts()
    all_errors = []
    pending_writes = []  # (path, new_text) — only flushed if the whole run is error-free

    for path in files:
        raw = open(path, encoding="utf-8").read()
        new_text, counts, errors = process_text(raw, path)
        all_errors.extend(errors)
        for k in totals:
            totals[k] += counts[k]
        base = os.path.basename(path)
        print(
            f"{base}: added={counts['n_added']} "
            f"already={counts['n_already_had_display']} "
            f"skipped_non_dimension={counts['n_skipped_non_dimension']} "
            f"errored={counts['n_errored']}"
        )
        if new_text is not None and new_text != raw:
            pending_writes.append((path, new_text))

    print(
        f"\nSummary: {{'n_added': {totals['n_added']}, "
        f"'n_already_had_display': {totals['n_already_had_display']}, "
        f"'n_skipped_non_dimension': {totals['n_skipped_non_dimension']}, "
        f"'n_errored': {totals['n_errored']}}} across {len(files)} files"
    )

    if all_errors:
        print("\nERRORS (no files written):", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    for path, new_text in pending_writes:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)

    return 0


def run_self_test():
    """Exercise the two-pass guarantees on synthetic inputs (no goldens touched)."""
    results = []

    def record(name, ok, detail=""):
        results.append((name, ok, detail))

    # 1. inline unknown category -> ERROR, no write.
    nt, c, errs = process_text('{"category": "BOGUS"}', "test1")
    record("1 inline-unknown -> error, no write", bool(errs) and nt is None, str(errs))

    # 2. inline unknown as LAST key, no trailing comma -> ERROR, no write.
    nt, c, errs = process_text('{"a": 1, "category": "BOGUS"}', "test2")
    record("2 inline-unknown-last-no-comma -> error, no write", bool(errs) and nt is None, str(errs))

    # 3. correct display, NON-ADJACENT to category -> already-correct, idempotent, verbatim.
    src3 = ('{"a": 1, "category": "Data Platform", "b": 2, '
            '"category_display": "Data Platform Modernization", "c": 3}')
    nt, c, errs = process_text(src3, "test3")
    record(
        "3 non-adjacent-correct -> idempotent verbatim",
        (not errs) and nt == src3 and c["n_already_had_display"] == 1 and c["n_added"] == 0,
        f"already={c['n_already_had_display']} added={c['n_added']} verbatim={nt == src3}",
    )

    # 4. present-but-WRONG display -> ERROR, NOT overwritten.
    src4 = '{"category": "Data Platform", "category_display": "WRONG"}'
    nt, c, errs = process_text(src4, "test4")
    record(
        "4 present-but-wrong -> error, not overwritten",
        bool(errs) and nt is None and "WRONG" in src4,
        str(errs),
    )

    # 5. absent display on a known dimension (canonical layout) -> exactly one add.
    src5 = '{\n  "category": "Data Platform",\n  "x": 1\n}'
    nt, c, errs = process_text(src5, "test5")
    ok5 = (
        not errs
        and nt is not None
        and c["n_added"] == 1
        and '"category_display": "Data Platform Modernization"' in nt
        and loads_strict(nt)["category_display"] == "Data Platform Modernization"
    )
    record("5 absent-on-dimension -> exactly one add", ok5, f"added={c['n_added']}")

    # 6. (bonus) duplicate category_display keys in input -> DuplicateKeyError.
    try:
        process_text(
            '{"category": "Data Platform", "category_display": "Data Platform Modernization", '
            '"category_display": "Data Platform Modernization"}',
            "test6",
        )
        ok6, detail6 = False, "no DuplicateKeyError raised"
    except DuplicateKeyError as e:
        ok6, detail6 = True, str(e)
    record("6 duplicate-key input -> rejected", ok6, detail6)

    all_ok = True
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        all_ok = all_ok and ok
        line = f"[{status}] {name}"
        if detail:
            line += f"  ({detail})"
        print(line)
    print(f"\nSELF-TEST: {'ALL PASS' if all_ok else 'FAILURES PRESENT'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
