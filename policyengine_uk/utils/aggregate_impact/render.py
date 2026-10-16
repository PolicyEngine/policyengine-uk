"""Render a comparison as a Markdown pull request comment."""

from __future__ import annotations

import math
from typing import Mapping, Optional

from . import COMMENT_MARKER
from .spec import Spec, fiscal_year_label

SECTIONS = (
    ("receipts", "Receipts by tax head"),
    ("spending", "Spending by benefit and service"),
    ("caseloads", "Caseloads"),
    ("balance", "Government balance, each component counted once"),
    ("model_totals", "Model totals"),
    ("double_counts", "Components the model counts twice"),
    ("household_totals", "Household income totals"),
    ("population", "Population"),
    ("poverty", "Poverty rates"),
    ("poverty_count", "People in poverty"),
    ("inequality", "Inequality"),
    ("deciles", "Mean household net income in each side's own deciles"),
    ("reforms", "Standard reform costings (change in gov_balance)"),
    ("reform_targets", "Standard reforms: change in each reform's target"),
)
MAX_FLAG_ROWS = 40


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def fmt_level(value, kind) -> str:
    if not _finite(value):
        return "n/a"
    if kind == "gbp":
        return f"£{value / 1e9:,.2f}bn"
    if kind == "gbp_household":
        return f"£{value:,.0f}"
    if kind == "count":
        return f"{value / 1e3:,.0f}k"
    if kind == "rate":
        return f"{100 * value:.1f}%"
    return f"{value:.4f}"


def fmt_change(value, kind) -> str:
    if value is None or not _finite(value):
        return "n/a"
    if value == 0:
        return "0"
    sign = "+" if value > 0 else "-"
    size = abs(value)
    if kind == "gbp":
        if size >= 1e9:
            return f"{sign}£{size / 1e9:,.2f}bn"
        if size >= 1e5:
            return f"{sign}£{size / 1e6:,.1f}m"
        return f"{sign}£{size:,.0f}"
    if kind == "gbp_household":
        return f"{sign}£{size:,.2f}" if size < 10 else f"{sign}£{size:,.0f}"
    if kind == "count":
        if size >= 1e3:
            return f"{sign}{size / 1e3:,.1f}k"
        return f"{sign}{size:,.0f}"
    if kind == "rate":
        return f"{sign}{100 * size:.2f}pp"
    return f"{sign}{size:.4f}"


def _table(header, rows) -> str:
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join(["---"] + ["---:"] * (len(header) - 1)) + "|",
    ]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _year_header(years):
    return [fiscal_year_label(int(y)) for y in years]


def _section_rows(summary, section):
    return [r for r in summary["rows"] if r["section"] == section]


def _changes_table(rows, years) -> str:
    changed = [r for r in rows if r["changed"]]
    if not changed:
        return "No change in any year."
    body = []
    for row in changed:
        if row["only_in"] == "head":
            cells = [_level_cell(row, y, "head") for y in years]
            body.append([f"{row['label']} (new: head levels)"] + cells)
        elif row["only_in"] == "base":
            cells = [_level_cell(row, y, "base") for y in years]
            body.append([f"{row['label']} (removed: base levels)"] + cells)
        else:
            body.append([row["label"]] + [_change_cell(row, y) for y in years])
    return _table(["Measure"] + _year_header(years), body)


def _mark(cell) -> str:
    # A total that leaves out a suppressed figure that year.
    return " †" if cell.get("excludes") else ""


def _level_cell(row, year, side) -> str:
    cell = row["values"][str(year)]
    if cell.get(f"{side}_suppressed"):
        return _SUPPRESSED_CELL
    return fmt_level(cell[side], row["kind"]) + _mark(cell)


def _change_cell(row, year) -> str:
    cell = row["values"][str(year)]
    if cell.get("delta") is None and (
        cell.get("base_suppressed") or cell.get("head_suppressed")
    ):
        return _SUPPRESSED_CELL
    return fmt_change(cell["delta"], row["kind"]) + _mark(cell)


# A figure from fewer than 10 records is not published (privacy.py).
_SUPPRESSED_CELL = "suppressed"


def _levels_table(rows, years) -> str:
    body = [
        [row["label"]] + [_level_cell(row, y, "head") for y in years] for row in rows
    ]
    return _table(["Measure (head)"] + _year_header(years), body)


def _details(summary_text, body) -> str:
    return f"<details>\n<summary>{summary_text}</summary>\n\n{body}\n\n</details>"


def _deciles(summary, years) -> str:
    deciles = summary.get("deciles") or {}
    if not deciles:
        return "Not available: both sides need household detail."
    present = [y for y in years if str(y) in deciles]
    if all(
        row["mean_change"] == 0 and not row.get("suppressed")
        for y in present
        for row in deciles[str(y)]
    ):
        if any(row.get("any_change") for y in present for row in deciles[str(y)]):
            return "Every decile's mean change rounds to £0 in every year."
        return "No household's net income changes in any year."
    labels = [row["decile"] for row in deciles[str(present[0])]]
    body = []
    for index, decile in enumerate(labels):
        cells = []
        for year in present:
            row = deciles[str(year)][index]
            if row.get("suppressed"):
                cells.append("fewer than 10 households change")
            elif row["mean_change"] == 0 or not _finite(row["mean_change"]):
                cells.append("0" if row["mean_change"] == 0 else "n/a")
            else:
                cells.append(
                    f"{fmt_change(row['mean_change'], 'gbp')} ({100 * row['relative_change']:+.1f}%)"
                )
        body.append([decile if decile == "all" else f"Decile {decile}"] + cells)
    text = (
        "Mean change in household net income per household, and as a share of the "
        "decile's base income; households stay in the base run's deciles.\n\n"
        + _table(["Base decile"] + _year_header(present), body)
    )
    winners = []
    for year in present:
        overall = deciles[str(year)][-1]
        if overall.get("suppressed"):
            winners.append(
                [fiscal_year_label(year)] + ["fewer than 10 households change"] * 2
            )
            continue
        winners.append(
            [
                fiscal_year_label(year),
                f"{100 * overall['share_gaining']:.1f}%",
                f"{100 * overall['share_losing']:.1f}%",
            ]
        )
    text += "\n\n" + _table(
        ["Year", "People gaining over £1", "People losing over £1"], winners
    )
    if summary.get("decile_notes"):
        text += "\n\n" + "\n".join(f"- {note}" for note in summary["decile_notes"])
    return text


def _flags(summary) -> str:
    flags = list(summary.get("flags") or [])
    flags += [
        {
            "label": f"Decile {f['decile']} household net income, relative",
            "year": f["year"],
            "kind": "relative",
            "base": None,
            "head": None,
            "delta": f["relative_change"],
            "limit": None,
            "section": "deciles",
        }
        for f in summary.get("decile_flags") or []
    ]
    if not flags:
        return "None."
    flags.sort(key=lambda f: -(abs(f["delta"]) / f["limit"]) if f.get("limit") else 0)
    shown = flags[:MAX_FLAG_ROWS]
    body = []
    for f in shown:
        if f["kind"] == "relative":
            body.append(
                [
                    f["label"],
                    fiscal_year_label(f["year"]),
                    "",
                    "",
                    f"{100 * f['delta']:+.2f}%",
                ]
            )
        else:
            body.append(
                [
                    f["label"],
                    fiscal_year_label(f["year"]),
                    fmt_level(f["base"], f["kind"]),
                    fmt_level(f["head"], f["kind"]),
                    fmt_change(f["delta"], f["kind"]),
                ]
            )
    text = _table(["Measure", "Year", "Base", "Head", "Change"], body)
    if len(flags) > len(shown):
        text += f"\n\n{len(flags) - len(shown)} more flags are in the report artifact."
    return text


def _check_list(checks, classification) -> list:
    out = []
    for check in checks:
        if check["classification"] != classification:
            continue
        details = check["head_details"] or check["base_details"]
        detail = f": {'; '.join(details[:3])}" if details else ""
        out.append(f"- {check['label']} (`{check['id']}`){detail}")
    return out


def _guard(summary) -> str:
    guard = (summary.get("head") or {}).get("guard") or {}
    if guard.get("status") != "ran":
        return f"Counted-once check not run: {guard.get('reason', 'unknown reason')}."
    components = guard.get("components", [])
    tested = [c for c in components if c["status"] != "skipped"]
    failed = [c for c in tested if c["status"] == "fail"]
    skipped = [c for c in components if c["status"] == "skipped"]
    lines = [
        f"Each of {len(tested)} components was raised by £1 per unit in "
        f"{fiscal_year_label(guard['year'])}, and every head of its totals was "
        "read household by household: its own head must rise by exactly £1, no "
        "other tax head may move, no other benefit may rise, and the model's own "
        "total must move by what its heads moved. A head that breaks a rule is "
        "measured again twice: with every other head held at its baseline value, "
        "and with every other head held at its value after the first £1 while the "
        "component rises again. It fails where either still shows the response. "
        f"{len(failed)} failed; {len(skipped)} were skipped."
    ]
    for c in failed:
        problems = c.get("problems") or [{"message": c.get("detail", "")}]
        lines.append(
            f"- `{c['variable']}`: " + "; ".join(p["message"] for p in problems)
        )
    for c in skipped:
        lines.append(f"- `{c['variable']}` skipped: {c.get('detail', '')}")
    for c in tested:
        for m in c.get("mediated") or []:
            moved = ", ".join(f"`{v}`" for v in m["via"]) or "none"
            where = (
                f"{m['households']:,} households"
                if m.get("households") is not None
                else "fewer than 10 households"
            )
            lines.append(
                f"- `{c['variable']}`: `{m['head']}` responds only through other "
                f"heads in {where} (other heads that moved there: {moved}; "
                f"{m['total']}; not a failure)"
            )
    for dc in guard.get("double_counts", []):
        state = "still contained" if dc["status"] == "pass" else "NO LONGER contained"
        lines.append(
            f"- declared double count `{dc['variable']}` is {state} in "
            f"`{dc['contained_in']}` (coefficient {dc['coefficient']:.3f}; {dc['issue']})"
        )
    return "\n".join(lines)


def _provenance(summary) -> str:
    rows = []
    for side in ("base", "head"):
        info = summary.get(side)
        if not info:
            rows.append([side, "no result", "", "", "", ""])
            continue
        provenance = info.get("provenance") or {}
        runtime = info.get("runtime") or {}
        rows.append(
            [
                side,
                f"{provenance.get('git_ref', '')} `{str(provenance.get('git_sha', ''))[:10]}`",
                f"uk {runtime.get('policyengine_uk')}, core {runtime.get('policyengine_core')}, py {runtime.get('python')} {runtime.get('machine', '')}",
                f"`{str(runtime.get('distributions_sha256', ''))[:12]}`",
                f"`{str((info.get('partition') or {}).get('sha256', ''))[:12]}`",
                f"{(info.get('timings') or {}).get('total', '')}s",
            ]
        )
    dataset = ((summary.get("head") or {}).get("provenance") or {}).get("dataset") or {}
    text = _table(
        ["Side", "Commit", "Runtime", "Environment hash", "Partition hash", "Time"],
        rows,
    )
    if dataset:
        text += (
            f"\n\nDataset: `{dataset.get('uri')}`, sha256 `{dataset.get('verified_sha256')}` "
            f"(verified on both sides), {dataset.get('data_package')} {dataset.get('data_version')}."
        )
    if summary.get("runtime_differences"):
        text += "\n\nRuntime differences:\n" + "\n".join(
            f"- {d}" for d in summary["runtime_differences"]
        )
    return text


def render(summary: Mapping, spec: Spec, context: Optional[Mapping] = None) -> str:
    """The full comment; sections are dropped from the end to fit GitHub's limit."""
    context = context or {}
    if summary["status"] == "skipped":
        notes = "\n".join(f"- {w}" for w in summary.get("warnings") or [])
        return f"{COMMENT_MARKER}\n## Aggregate impact on certified data: skipped\n\n{notes}\n"
    years = summary.get("years") or spec.years
    regressions = [c for c in summary["checks"] if c["classification"] == "regression"]
    pre_existing = [
        c for c in summary["checks"] if c["classification"] == "pre_existing"
    ]
    new_warnings = [
        c for c in summary["checks"] if c["classification"] == "new_warning"
    ]
    fixed = [c for c in summary["checks"] if c["classification"] == "fixed"]
    flag_count = len(summary.get("flags") or []) + len(
        summary.get("decile_flags") or []
    )
    verdict = "FAIL" if summary["status"] == "fail" else "pass"

    head_prov = (summary.get("head") or {}).get("provenance") or {}
    base_prov = (summary.get("base") or {}).get("provenance") or {}
    dataset = head_prov.get("dataset") or {}
    parts = [
        COMMENT_MARKER,
        f"## Aggregate impact on certified data: {verdict}",
        "",
        (
            f"Base `{str(base_prov.get('git_sha', '?'))[:10]}` against head "
            f"`{str(head_prov.get('git_sha', '?'))[:10]}`, both on `{dataset.get('path', '?')}` "
            f"({dataset.get('data_package', '')} {dataset.get('data_version', '')}, sha256 "
            f"`{str(dataset.get('verified_sha256', '?'))[:12]}`), fiscal years "
            f"{fiscal_year_label(years[0])} to {fiscal_year_label(years[-1])}. Each year is a full "
            "microsimulation run on each side."
        ),
        "",
        (
            f"**Checks:** {len(regressions)} broken by this change, {len(pre_existing)} failing on "
            f"both sides, {len(fixed)} fixed. **Moves flagged for review:** {flag_count} "
            "(thresholds in `report_spec.yaml`; a flag does not fail the job)."
        ),
    ]
    if context.get("run_url"):
        parts.append(f"\n[Workflow run and full report]({context['run_url']})")
    if summary["failures"]:
        parts += ["", "### Failures", ""] + [f"- {f}" for f in summary["failures"]]
    if new_warnings:
        parts += ["", "### New warnings", ""] + _check_list(
            summary["checks"], "new_warning"
        )
    if summary["warnings"]:
        parts += ["", "### Notes", ""] + [f"- {w}" for w in summary["warnings"]]
    if fixed:
        parts += ["", "### Fixed by this change", ""] + _check_list(
            summary["checks"], "fixed"
        )
    parts += ["", "### Moves flagged for review", "", _flags(summary)]

    unchanged = []
    for section, title in SECTIONS:
        rows = _section_rows(summary, section)
        if not rows:
            continue
        if not any(row["changed"] for row in rows):
            unchanged.append(title[:1].lower() + title[1:])
            continue
        parts += ["", f"### {title}", "", _changes_table(rows, years)]
    parts += ["", "### Household net income by decile", "", _deciles(summary, years)]
    if unchanged:
        parts += ["", "**No change in any year:** " + "; ".join(unchanged) + "."]

    optional = []
    if pre_existing:
        optional.append(
            _details(
                f"Checks failing on both base and head ({len(pre_existing)})",
                "\n".join(_check_list(summary["checks"], "pre_existing")),
            )
        )
    optional.append(_details("Counted-once check", _guard(summary)))
    optional.append(_details("Provenance", _provenance(summary)))
    for section, title in SECTIONS:
        rows = _section_rows(summary, section)
        if rows:
            optional.append(
                _details(f"{title}: head levels", _levels_table(rows, years))
            )

    text = "\n".join(parts)
    limit = spec.max_comment_characters
    note = "\n\n_Some detail was left out to fit a GitHub comment; the workflow artifact has all of it._"
    kept = []
    for block in optional:
        candidate = text + "\n\n" + "\n\n".join(kept + [block])
        if len(candidate) + len(note) > limit:
            continue
        kept.append(block)
    if kept:
        text += "\n\n" + "\n\n".join(kept)
    if len(kept) < len(optional):
        text += note
    if len(text) > limit:
        text = text[: limit - len(note) - 1] + note
    return text + "\n"
