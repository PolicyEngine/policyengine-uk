"""Data protection: only aggregates may leave the aggregate-impact job.

The certified dataset is licensed survey microdata. The measurement keeps
household-level detail for the decile comparison under ``private/``; these
tests fail if the workflow could publish it, or could put the dataset where
other workflows can read it.
"""

import json
from pathlib import Path

import numpy as np
import yaml

from policyengine_uk.utils.aggregate_impact.measure import (
    HOUSEHOLDS_FILE,
    PRIVATE_DIRECTORY,
    read_result,
    write_result,
)

REPO = Path(__file__).resolve().parents[3]
WORKFLOW = REPO / ".github" / "workflows" / "aggregate-impact.yaml"
ALLOWED_UPLOAD_PATHS = {"report"}


def steps():
    workflow = yaml.safe_load(WORKFLOW.read_text())
    return [step for job in workflow["jobs"].values() for step in job["steps"]]


def test_only_the_aggregate_report_is_uploaded():
    uploads = [s for s in steps() if "upload-artifact" in str(s.get("uses", ""))]
    assert uploads, "the report should be uploaded"
    for step in uploads:
        paths = {p.strip() for p in str(step["with"]["path"]).splitlines() if p.strip()}
        assert paths <= ALLOWED_UPLOAD_PATHS, paths


def test_the_dataset_is_never_cached():
    for step in steps():
        assert "actions/cache" not in str(step.get("uses", "")), step.get("name")


def test_nothing_private_is_copied_into_the_report():
    text = WORKFLOW.read_text()
    copies = [
        line.strip() for line in text.splitlines() if line.strip().startswith("cp ")
    ]
    for line in copies:
        if "report/" in line:
            assert line.split()[1].endswith("result.json"), line
    assert f"{PRIVATE_DIRECTORY}/" not in "\n".join(copies)
    assert HOUSEHOLDS_FILE not in "\n".join(copies)


def test_the_job_runs_both_sides_itself():
    workflow = yaml.safe_load(WORKFLOW.read_text())
    assert list(workflow["jobs"]) == ["report"], (
        "base and head must be measured in one job, so that household detail "
        "never has to travel between jobs as an artifact"
    )
    assert not [s for s in steps() if "download-artifact" in str(s.get("uses", ""))]


def test_household_detail_is_written_only_under_private(tmp_path):
    households = {
        "2026": {
            "household_id": np.arange(5),
            "household_weight": np.ones(5),
            "household_count_people": np.ones(5),
            "decile": np.arange(5),
            "income": np.linspace(1, 2, 5),
        }
    }
    write_result(tmp_path, {"status": "ok", "metrics": []}, households)
    top_level = sorted(p.name for p in tmp_path.iterdir())
    assert top_level == [PRIVATE_DIRECTORY, "result.json"]
    assert (tmp_path / PRIVATE_DIRECTORY / HOUSEHOLDS_FILE).exists()
    result, loaded = read_result(tmp_path)
    assert json.loads((tmp_path / "result.json").read_text()) == result
    assert np.array_equal(loaded["2026"]["income"], households["2026"]["income"])
