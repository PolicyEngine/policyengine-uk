"""Bounded, nonfinancial observations of selected measurement windows."""

from __future__ import annotations

import cProfile
import json
import math
from pathlib import Path
import sys
import time
from types import CodeType


SCHEMA = "policyengine-uk-aggregate-infra-profile/1"
MAX_ROWS = 50
MAX_BYTES = 65_536
PREFIX = "aggregate-impact-infra-profile "

# Match path components internally; publish only these literal identifiers.
_ALLOWLIST = (
    *(
        (
            f"policyengine_uk.utils.geography.py:{name}",
            (("policyengine_uk", "utils", "geography.py"),),
            name,
        )
        for name in (
            "_names",
            "_cell_mask",
            "input_facts",
            "_resolve",
            "resolved_region",
            "merge_geography_formula",
        )
    ),
    *(
        (
            f"policyengine_uk.simulation.py:Simulation.{name}",
            (("policyengine_uk", "simulation.py"),),
            f"Simulation.{name}",
        )
        for name in ("calculate", "_calculate", "clone")
    ),
    (
        "policyengine_uk.microsimulation.py:Microsimulation.calculate",
        (("policyengine_uk", "microsimulation.py"),),
        "Microsimulation.calculate",
    ),
    *(
        (
            f"policyengine_core.simulations.simulation.py:Simulation.{name}",
            (("policyengine_core", "simulations", "simulation.py"),),
            f"Simulation.{name}",
        )
        for name in ("calculate", "_calculate", "clone")
    ),
    (
        "policyengine_core.holders.holder.py:Holder.get_array",
        (("policyengine_core", "holders", "holder.py"),),
        "Holder.get_array",
    ),
    *(
        (
            f"aggregate_impact.guard.py:{name}",
            (
                ("policyengine_uk", "utils", "aggregate_impact", "guard.py"),
                ("pe_uk_aggregate_impact", "guard.py"),
            ),
            name,
        )
        for name in (
            "_perturb",
            "discard_formula_results",
            "_set_guard_value",
            "_head_arrays",
            "_raw",
            "_household",
        )
    ),
    *(
        (
            f"aggregate_impact.measure.py:{name}",
            (
                ("policyengine_uk", "utils", "aggregate_impact", "measure.py"),
                ("pe_uk_aggregate_impact", "measure.py"),
            ),
            name,
        )
        for name in ("measure_year", "array", "weighted_total", "baseline_records")
    ),
    (
        "policyengine_uk.utils.geography.py:country_from_region",
        (("policyengine_uk", "utils", "geography.py"),),
        "country_from_region",
    ),
    (
        "policyengine_core.enums.enum.py:Enum.encode",
        (("policyengine_core", "enums", "enum.py"),),
        "Enum.encode",
    ),
    (
        "numpy.lib._arraysetops_impl.py:isin",
        (("numpy", "lib", "_arraysetops_impl.py"),),
        "isin",
    ),
)


def _literal_id(code):
    if not isinstance(code, CodeType):
        return None
    parts = Path(code.co_filename).parts
    for literal, suffixes, qualname in _ALLOWLIST:
        if code.co_qualname == qualname and any(
            len(parts) >= len(suffix) and parts[-len(suffix) :] == suffix
            for suffix in suffixes
        ):
            return literal
    return None


def _safe_rows(entries, *, window="first_ordinary_year"):
    """Return observed allowlisted numeric statistics, never raw profile data."""
    rows = {}
    for entry in entries:
        try:
            literal = _literal_id(entry.code)
            if literal is None or (
                literal.startswith("aggregate_impact.guard.py:")
                and window != "first_counted_once_probe"
            ):
                continue
            calls, recursive = entry.callcount, entry.reccallcount
            own, cumulative = entry.inlinetime, entry.totaltime
            if (
                type(calls) is not int
                or type(recursive) is not int
                or not 0 <= recursive <= calls
                or type(own) not in (int, float)
                or type(cumulative) not in (int, float)
                or not all(
                    math.isfinite(value) and value >= 0 for value in (own, cumulative)
                )
            ):
                continue
            before = rows.get(literal)
            row = {
                "id": literal,
                "calls": calls + (before["calls"] if before else 0),
                "primitive_calls": calls
                - recursive
                + (before["primitive_calls"] if before else 0),
                "self_seconds": own + (before["self_seconds"] if before else 0),
                "cumulative_seconds": cumulative
                + (before["cumulative_seconds"] if before else 0),
            }
            if all(
                math.isfinite(row[key])
                for key in ("self_seconds", "cumulative_seconds")
            ):
                rows[literal] = row
        except Exception:  # noqa: BLE001 - malformed diagnostics do not affect measurement
            continue
    return [rows[key] for key in sorted(rows)][:MAX_ROWS]


def _publish(out, record):
    try:
        line = json.dumps(
            record, sort_keys=True, allow_nan=False, separators=(",", ":")
        )
        if len((PREFIX + line + "\n").encode("utf-8")) > MAX_BYTES:
            return
    except Exception:  # noqa: BLE001 - no diagnostic error text is published
        return
    try:
        destination = Path(out) / "infra-profile.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as stream:
            stream.write(line + "\n")
            stream.flush()
    except Exception:  # noqa: BLE001 - stderr is an independent sink
        pass
    try:
        print(PREFIX + line, file=sys.stderr, flush=True)
    except Exception:  # noqa: BLE001 - diagnostics cannot change the financial result
        pass


_ORPHANED_PROFILE = None


class FirstYearProfiler:
    """One best-effort profile, with no persisted paths, values or raw statistics.

    CPython 3.11 uses the legacy hook; 3.12--3.14 cProfile uses monitoring.
    Monitoring ownership is cooperative: its public tool name is not an
    object-identity guarantee against a caller manually hijacking the same ID.
    """

    def __init__(self, out, label, *, window="first_ordinary_year"):
        if window not in ("first_ordinary_year", "first_counted_once_probe"):
            raise ValueError("Unknown infrastructure profile window")
        self.window = window
        self.out = out
        self.label = label if label in ("base", "head") else "other"
        self._attempted = False
        self._finished = False
        self._profile = None
        self._reason = None
        self._started = None
        self._year = None
        self._monitoring = None
        self._enabled = False

    @staticmethod
    def _monitoring_backend():
        return getattr(sys, "monitoring", None)

    def _owns_profile(self):
        if self._monitoring is None:
            return sys.getprofile() is self._profile
        return self._monitoring.get_tool(self._monitoring.PROFILER_ID) == "cProfile"

    def _quarantine_profile(self):
        global _ORPHANED_PROFILE
        # Retain at most one lost enabled observer across CLI windows:
        # its native destructor can clear a caller's legacy hook. Once retained,
        # no later observer may activate; never inspect or publish its statistics.
        if _ORPHANED_PROFILE is None:
            _ORPHANED_PROFILE = self._profile
        self._enabled = False

    def _retire_profile(self):
        try:
            if not self._owns_profile():
                if self._enabled:
                    self._quarantine_profile()
                return False
            self._profile.disable()
            self._enabled = False
            return True
        except BaseException:
            # Retain before unwinding: an enabled native destructor may clear
            # a foreign hook. Propagate genuine interrupts without replacing them.
            if self._profile is not None:
                self._quarantine_profile()
            raise

    def __call__(self, event, phase, **scope):
        if phase != self.window:
            return
        if event == "start" and not self._attempted:
            self._attempted = True
            year = scope.get("year")
            if type(year) is not int:
                return
            self._year = year
            self._started = time.monotonic()
            try:
                if _ORPHANED_PROFILE is not None:
                    self._reason = "observer_unavailable"
                    return
                self._monitoring = self._monitoring_backend()
                if sys.getprofile() is not None or (
                    self._monitoring is not None
                    and self._monitoring.get_tool(self._monitoring.PROFILER_ID)
                    is not None
                ):
                    self._reason = "preexisting_profiler"
                    return
                self._profile = cProfile.Profile()
                self._profile.enable()
                self._enabled = True
            except Exception:  # noqa: BLE001 - the financial call still runs
                self._reason = "observer_unavailable"
                if self._profile is not None:
                    try:
                        self._retire_profile()
                    except Exception:  # noqa: BLE001 - best-effort startup cleanup
                        if self._enabled:
                            self._quarantine_profile()
                self._profile = None
            except BaseException:
                # enable() may have activated natively before the assignment to
                # _enabled. Do not destroy that uncertain instance on interrupt.
                if self._profile is not None:
                    self._quarantine_profile()
                raise
        elif (
            event == "stop"
            and self._attempted
            and not self._finished
            and self._year is not None
        ):
            self._finished = True
            completed = scope.get("completed") is True
            rows = []
            try:
                retired = False
                if self._profile is not None:
                    if self._enabled:
                        retired = self._retire_profile()
                    if not retired:
                        self._reason = "observer_unavailable"
                elapsed = time.monotonic() - self._started
                if not math.isfinite(elapsed) or elapsed < 0:
                    raise ValueError
                if retired and self._reason is None:
                    if self.window == "first_ordinary_year":
                        rows = _safe_rows(self._profile.getstats())
                    else:
                        rows = _safe_rows(self._profile.getstats(), window=self.window)
            except Exception:  # noqa: BLE001 - fixed reason, no exception text
                if self._enabled:
                    self._quarantine_profile()
                self._reason = "observer_unavailable"
                elapsed = 0.0
                rows = []
            finally:
                self._profile = None
            record = {
                "schema": SCHEMA,
                "status": "ok" if completed else "interrupted",
                "label": self.label,
                "year": self._year,
                "completed": completed,
                "window_seconds": elapsed,
                "functions": rows,
            }
            if self._reason is not None:
                record["status"] = (
                    "skipped"
                    if self._reason == "preexisting_profiler"
                    else "unavailable"
                )
                record["reason"] = self._reason
            if self.window != "first_ordinary_year":
                record["window"] = self.window
            _publish(self.out, record)
