# Projection horizon resume, 12 October 2026

- Assigned workspace starts at `6d89338abf16`; restored the existing PR #2376
  head `db9e0ac16063dd386e60644834bd328153e958ce` without touching the caller's
  worktree. The sandbox denies writes to shared Git metadata, so commits use
  workspace-local `.workspace-git` and push to `fix-projection-horizon-obr`.
- Read all required repository engineering guidance and both contribution
  guides. Three independent read-only audits checked mechanism, coverage and
  tests. Core is 3.32.27, matching the lock.
- Rehashed enhanced FRS 2024-25: SHA-256
  `5ba399ea5ab9a6c7d4e9aaf6c623080beb34d9ad5f330f6244dbad72b8d960b6`.
  Saved `measure_all.py` PID 43401 has exited; all three JSON outputs exist.
- Corrected the decomposition: tax-free savings exemption becomes zero when
  its ISA-interest source is absent; Northern Ireland domestic rates were
  mislabeled "NI rates"; flat record values can still have rising weighted
  totals. Attribution is cumulative and order-dependent.
- Pension Credit capital's -1 is real after the horizon. Existing situation
  tests intentionally expire direct programme inputs. Preserve that contract;
  record legacy dataset materialisation as a follow-up, rather than changing
  formula semantics. Added small regression tests for legacy capital and
  savings takeover, plus reported State Pension within/beyond the horizon.
- Growth source dates, processed fiscal parameter dates and cumulative-index
  coverage are different. No new forecast values were added. #2274's finite
  CGT scenarios need a scenario-specific cap while the legacy default remains
  2032; do not manufacture EOT projections beyond 2030.
- Saved cost_before.json actually reports 1.543 GB RSS, not the 2.18 GB in
  the resume prompt. Its 314-second load was heavily contended; running a new
  sequential before/after pair against the same code with only the horizon
  changed. Compressor gates and a 20 GB RSS monitor are active.
- Pushed `eaf48e9`: clarified docs and synthetic regression tests. Created
  tracking issue #2378. Equivalent Ruff format/check on touched Python files
  passed using the read-only existing r5 venv; a fresh uv install was stopped
  after slow package preparation rather than modifying dependencies elsewhere.
- New sequential costs completed: before load 33.2s / RSS 2.220 GB, 2032
  overall peak 2.529 GB; after load 13.3s / RSS 2.646 GB, overall peak 2.921 GB.
  Compressor gates 7.898/7.850 GB. Timing is host-dependent; not a speed claim.
  Isolated before HNI matches saved cost but differs from inherited full-period
  impact; after HNI matches inherited impact. Recorded this verification gap.
- Running eight focused test files serially, including the full changed file,
  no-economic-assumptions, rents, council tax, domestic rates, capital semantics,
  thresholds and statutory triple-lock inputs. No test_economic_assumptions*
  filename exists at this checkpoint; the unrelated dataframe test is excluded.
- Next: finish tests, final report/PR update, independent exact-head review and
  handoffs.jsonl.
- Initial pytest collection was interrupted after 774.77s with no tests run.
  Stack trace located the stall in Hypothesis 6.168.2 `_get_local_constants`,
  mining dynamically imported variable module source. Restarted the same
  serial tests with only that optional local-source heuristic disabled in the
  external verification harness; explicit strategies/example counts unchanged.
  Source tests/dependencies are not patched. Full `make format` passed across
  1,363 Python files before the report/cost commit `2765bd6` was pushed.
- The fresh-system run eventually stopped with 8 projection tests passed in
  954.70s; the interrupt was delayed by the sandbox. Confirmed the process had
  exited before restarting. The final run uses the repository's existing
  cloned-system constructor seam in the local harness, preserving independent
  variable and parameter state while avoiding repeated source loading. It
  still disables optional Hypothesis source-constant mining; tests unchanged.
- Fresh independent team review at exact `2765bd6e01f0b773ec197a5b94209dd6afbc213a`
  found no blocking issues. Nonblocking gap: student-loan cohort behavior in
  2031–2032 is not directly exercised by the new fixture. Saved review is
  `.verification/team-head-review.md`.
- Submitted requested isolated Subfleet hard review with an explicit prompt
  file, job `20261012-054543-uk-horizon-2032-head-review`; queued for admission.
  Prompt-file routing avoids writes to the inaccessible global inbox, and its
  immutable review checkout is inside this assigned workspace.
- The cloned-system retry exited 139 during import while the faulthandler
  timer was emitting an incomplete import-stack dump. No tests ran in that
  process. Removed the diagnostic timer and am completing a fresh locked
  workspace-local environment with bounded uv installation concurrency before
  rerunning. No simulation process is still active from the failed retry.
- Fresh locked environment completed (Python 3.13.15, Core 3.32.27); full
  serial suite now at 97%. All nine initial projection tests passed; one
  unchanged September-CPI property failed, with its footer still pending.
- Requested Subfleet hard review at `2765bd6` completed with P2: storing extra
  years suppresses Core growth for unmapped salary sacrifice/housing charges.
  Added post-2030 compatibility using each variable's cumulative index,
  preserving projections through 2030 and explicit FY26/27 energy exclusions.
  Registry covers twelve eligible inputs, four present in this H5. Resetting
  growth now includes them. Tests cover all twelve, reset, energy exclusions
  and a second Hypothesis ratio property. Full make format passed again.
- Next: run the changed tests after this correction, refresh survey impacts
  and after-cost, then obtain independent review at the corrected head.
