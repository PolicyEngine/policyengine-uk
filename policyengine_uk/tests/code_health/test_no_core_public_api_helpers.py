"""No code here may use the policyengine-core helpers that call the Public API.

``Reform.from_api``, ``Reform.api_id`` and ``policyengine_core.charts.api``
send HTTP requests to api.policyengine.org, and policyengine-core is removing
them. ``policyengine_core.charts`` also re-exports that module's
``intra_decile_chart`` and ``decile_chart``. Code that still uses any of them,
including a test that replaces ``requests.get`` in
``policyengine_core.reforms.reform``, fails as soon as a policyengine-core
release without them is installed.
"""

import re
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
THIS_FILE = Path(__file__).resolve()

REMOVED_HELPER_REFERENCE = re.compile(
    r"\.from_api\b"
    r"|\.api_id\b"
    r"|policyengine_core\.charts\.api\b"
    r"|\bget_api_chart_data\b"
    r"|\bintra_decile_chart\b"
    r"|\bdecile_chart\b"
    r"|policyengine_core\.reforms\.reform\.requests\b"
)


def removed_helper_references(source_text: str) -> list[str]:
    return sorted(
        {match.group(0) for match in REMOVED_HELPER_REFERENCE.finditer(source_text)}
    )


@pytest.mark.parametrize(
    "source_text, expected_reference",
    [
        pytest.param(
            'Reform.from_api("1", country_id="uk")', ".from_api", id="from_api"
        ),
        pytest.param("policy_id = reform.api_id", ".api_id", id="api_id"),
        pytest.param(
            "from policyengine_core.charts.api import get_api_chart_data",
            "policyengine_core.charts.api",
            id="chart_module",
        ),
        pytest.param(
            "chart_data = charts.get_api_chart_data()",
            "get_api_chart_data",
            id="get_api_chart_data",
        ),
        pytest.param(
            'monkeypatch.setattr("policyengine_core.reforms.reform.requests.get", '
            "fake_get)",
            "policyengine_core.reforms.reform.requests",
            id="fake_requests_get",
        ),
        # policyengine_core.charts re-exports the chart functions of
        # policyengine_core.charts.api, so they can be used without naming it.
        pytest.param(
            "from policyengine_core.charts import decile_chart",
            "decile_chart",
            id="decile_chart",
        ),
        pytest.param(
            "from policyengine_core.charts import intra_decile_chart",
            "intra_decile_chart",
            id="intra_decile_chart",
        ),
        pytest.param(
            "from policyengine_core.charts import api\nfigure = api.decile_chart()",
            "decile_chart",
            id="chart_module_imported_as_api",
        ),
    ],
)
def test_removed_helper_pattern_finds_each_helper(source_text, expected_reference):
    assert expected_reference in removed_helper_references(source_text)


@pytest.mark.parametrize(
    "source_text",
    [
        pytest.param('Reform.from_dict(changes, country_id="uk")', id="from_dict"),
        pytest.param(
            "from policyengine_core.charts import format_fig, BLUE",
            id="chart_formatting",
        ),
    ],
)
def test_removed_helper_pattern_ignores_supported_core_functions(source_text):
    assert removed_helper_references(source_text) == []


def test_code_does_not_use_core_public_api_helpers():
    references_by_file = {}
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        if path.resolve() == THIS_FILE:
            continue
        references = removed_helper_references(path.read_text())
        if references:
            references_by_file[str(path.relative_to(PACKAGE_ROOT))] = references
    assert not references_by_file, (
        f"These files use policyengine-core helpers that call the Public API "
        f"over HTTP and are being removed: {references_by_file}. Build reforms "
        "with Reform.from_dict instead."
    )
