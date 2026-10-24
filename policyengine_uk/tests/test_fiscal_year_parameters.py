"""
Tests for UK fiscal year parameter handling.

The UK fiscal year runs April 6 to April 5. PolicyEngine UK converts
parameters to use fiscal year values by sampling at April 30 of each year.

This test suite verifies that annual period queries (e.g., param("2026"))
return the correct fiscal year values, especially for policy changes
that take effect on April 6.

Key policy example:
- Two-child limit repeal: limit=2 until April 5, 2026, then infinity
  from April 6, 2026
"""

import pytest
from policyengine_uk import CountryTaxBenefitSystem


@pytest.fixture(scope="module")
def uk_system():
    """Create a UK tax-benefit system for testing."""
    return CountryTaxBenefitSystem()


class TestTwoChildLimitRepeal:
    """Tests for the two-child limit repeal on April 6, 2026."""

    def test_two_child_limit_fiscal_year_2025(self, uk_system):
        """Test that the two-child limit is 2 for fiscal year 2025/26."""
        params = uk_system.get_parameters_at_instant("2025")
        child_limit = params.gov.dwp.universal_credit.elements.child.limit.child_count
        assert child_limit == 2

    def test_two_child_limit_fiscal_year_2026(self, uk_system):
        """Test that the two-child limit is infinity for fiscal year 2026/27.

        This is the key test case - the repeal happens on April 6, 2026.
        When querying for "2026", the system should use April 30, 2026
        as the reference date, which is AFTER the repeal date.
        """
        params = uk_system.get_parameters_at_instant("2026")
        child_limit = params.gov.dwp.universal_credit.elements.child.limit.child_count
        assert child_limit == float("inf"), (
            f"Expected infinity for 2026 fiscal year, got {child_limit}. "
            "The fiscal year conversion may not be covering 2026."
        )

    def test_annual_query_reflects_fiscal_year(self, uk_system):
        """
        Test that annual queries return fiscal year values.

        For year 2026, the fiscal year is April 6, 2026 to April 5, 2027.
        The two-child limit is repealed on April 6, 2026, so:
        - 2025 should be 2 (fiscal year 2025/26)
        - 2026 should be infinity (fiscal year 2026/27)
        - 2027 should be infinity (fiscal year 2027/28)
        """
        params_2025 = uk_system.get_parameters_at_instant("2025")
        params_2026 = uk_system.get_parameters_at_instant("2026")
        params_2027 = uk_system.get_parameters_at_instant("2027")

        limit_2025 = (
            params_2025.gov.dwp.universal_credit.elements.child.limit.child_count
        )
        limit_2026 = (
            params_2026.gov.dwp.universal_credit.elements.child.limit.child_count
        )
        limit_2027 = (
            params_2027.gov.dwp.universal_credit.elements.child.limit.child_count
        )

        assert limit_2025 == 2
        assert limit_2026 == float("inf")
        assert limit_2027 == float("inf")


class TestFiscalYearBoundary:
    """Tests for fiscal year boundary behavior.

    Note: After fiscal year conversion, the entire year is set to the
    April 30 value. This means January-March dates return the fiscal
    year value for that calendar year, not the previous fiscal year.
    """

    def test_january_2026_returns_fiscal_year_2026_value(self, uk_system):
        """January 2026 should return fiscal year 2026/27 value.

        After fiscal year conversion, the year 2026 is set to the
        April 30, 2026 value (infinity, post-repeal).
        """
        params = uk_system.get_parameters_at_instant("2026-01-15")
        child_limit = params.gov.dwp.universal_credit.elements.child.limit.child_count
        # This returns inf because the whole year 2026 is set to fiscal year value
        assert child_limit == float("inf")

    def test_december_2025_returns_fiscal_year_2025_value(self, uk_system):
        """December 2025 should return fiscal year 2025/26 value."""
        params = uk_system.get_parameters_at_instant("2025-12-15")
        child_limit = params.gov.dwp.universal_credit.elements.child.limit.child_count
        # The year 2025 is set to April 30, 2025 value (2, pre-repeal)
        assert child_limit == 2


class TestMidYearRateChanges:
    """Tests for changes taking effect part-way through a fiscal year.

    Sampling one date per year drops any change taking effect after it.
    Parameters carrying `fiscal_year_blend: true` are day-weighted across
    the year instead.
    """

    # Fiscal year 2024-25 runs 6 April 2024 to 5 April 2025: 207 days at the
    # rates in force before 30 October 2024, then 158 days at the rates after.
    DAYS_BEFORE = 207
    DAYS_AFTER = 158
    TOTAL_DAYS = DAYS_BEFORE + DAYS_AFTER

    def blended(self, before, after):
        return (before * self.DAYS_BEFORE + after * self.DAYS_AFTER) / self.TOTAL_DAYS

    @pytest.mark.parametrize(
        "rate_name, before, after",
        [("basic_rate", 0.10, 0.18), ("higher_rate", 0.20, 0.24)],
    )
    def test_cgt_rates_blend_across_the_split_year(self, rate_name, before, after):
        """2024-25 carries both statutory rates, so the year takes their average."""
        system = CountryTaxBenefitSystem()
        rates = {
            year: getattr(
                system.get_parameters_at_instant(str(year)).gov.hmrc.cgt, rate_name
            )
            for year in (2023, 2024, 2025)
        }

        assert rates[2023] == pytest.approx(before)
        assert rates[2024] == pytest.approx(self.blended(before, after))
        assert rates[2025] == pytest.approx(after)

    def test_cgt_rate_rise_takes_effect_from_the_statutory_date(self):
        """Finance Act 2025 s.7 applies to disposals from 30 October 2024.

        Read before fiscal year conversion, which is what the statutory dates
        feed. Regression test for dating the rise to 6 April 2025, which moved
        a change the legislation makes in 2024-25 into the following year.
        """
        import policyengine_uk
        from pathlib import Path
        from policyengine_core.parameters import ParameterNode

        parameters = ParameterNode(
            directory_path=str(Path(policyengine_uk.__file__).parent / "parameters")
        )
        higher_rate = parameters.gov.hmrc.cgt.higher_rate

        assert higher_rate("2024-10-29") == pytest.approx(0.20)
        assert higher_rate("2024-10-30") == pytest.approx(0.24)

    def test_blending_is_opt_in(self, uk_system):
        """Parameters without the flag keep one sampled value for the year.

        National Insurance rates fell part-way through 2022-23, and the year
        still takes the rate in force at its start rather than an average.
        Whether to blend is a decision per parameter: a transaction is taxed
        at the rate in force on its date, not at a yearly average.
        """
        parameters = uk_system.get_parameters_at_instant("2022")
        employee_rates = parameters.gov.hmrc.national_insurance.class_1.rates.employee

        assert employee_rates.main == pytest.approx(0.1325)


class TestScenarioOverrides:
    """Annual Scenario overrides name UK fiscal years.

    Written as calendar years, an override's final five months fell back to
    prior law and fiscal-year conversion blended the two: an override of 0.5
    on a blended CGT rate resolved to 0.42. The override now covers 6 April
    to 5 April.
    """

    def _reformed(self):
        from policyengine_uk import Microsimulation
        from policyengine_uk.model_api import Scenario

        return Microsimulation(
            situation={
                "people": {
                    "person": {
                        "age": {2025: 45},
                        "adjusted_net_income": {2025: 20_000},
                        "capital_gains": {2025: 23_000},
                    }
                },
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {"household": {"members": ["person"]}},
            },
            scenario=Scenario(
                parameter_changes={
                    "gov.hmrc.cgt.basic_rate": {"2025": 0.5},
                    # The tax on the gains as given, without the response.
                    "gov.simulation.capital_gains_responses.elasticity": {"2025": 0},
                }
            ),
        )

    def test_override_applies_at_full_strength(self):
        sim = self._reformed()
        rate = sim.tax_benefit_system.parameters.gov.hmrc.cgt.basic_rate

        assert rate("2025") == pytest.approx(0.5)
        cgt = sim.calculate("capital_gains_tax", 2025).values[0]
        assert cgt == pytest.approx(10_000.0)

    def test_override_leaves_other_years_on_law(self):
        """The split 2024-25 blend and the 2026 reversion both survive."""
        sim = self._reformed()
        rate = sim.tax_benefit_system.parameters.gov.hmrc.cgt.basic_rate

        assert rate("2024") == pytest.approx((0.10 * 207 + 0.18 * 158) / 365)
        assert rate("2026") == pytest.approx(0.18)


class TestFiscalYearCoverage:
    """Tests to verify fiscal year conversion covers all needed years."""

    @pytest.mark.parametrize("year", [2025, 2026, 2027, 2028, 2029, 2030, 2040])
    def test_year_in_conversion_range(self, uk_system, year):
        """
        Test that years from 2025-2040 can be queried.

        This verifies that the fiscal year conversion range covers
        all years needed for long-term projections.
        """
        params = uk_system.get_parameters_at_instant(str(year))
        assert params is not None
        # Verify we can access a parameter
        pa = params.gov.hmrc.income_tax.allowances.personal_allowance.amount
        assert pa is not None
        assert pa > 0


# #1436: synthetic engineering histories, not proposed statutory rates.
def _future_1436_tree(*, blend=False, preserve=False, values=None):
    from policyengine_core.parameters import ParameterNode

    timeline = values or {
        "2010-01-01": 50,
        "2041-01-01": 100,
        "2041-04-06": 200,
        "2041-10-01": 300,
    }
    leaf = {
        "description": "Synthetic fiscal conversion fixture",
        "metadata": {
            "label": "synthetic fixture",
            "fiscal_year_blend": blend,
            "preserve_calendar_dates": preserve,
            "unit": "currency-GBP",
        },
        "values": timeline,
    }
    return ParameterNode("", data={"gov": {"future": leaf}, "market": leaf})


def _future_1436_records(parameter):
    import copy

    return [
        (
            entry.name,
            entry.instant_str,
            copy.deepcopy(entry.value),
            copy.deepcopy(entry.metadata),
            entry.file_path,
        )
        for entry in parameter.values_list
    ]


def _future_1436_eager_reference(root, blend):
    """Retain the old26 writes, with an independent daily sampling oracle."""
    import datetime

    leaf = root.gov.future
    entries = [(entry.instant_str, entry.value) for entry in leaf.values_list]

    def stated(day):
        eligible = [(key, value) for key, value in entries if key <= str(day)]
        return max(eligible, key=lambda item: item[0])[1] if eligible else None

    values = {}
    for year in range(2015, 2041):
        if blend:
            day = first = datetime.date(year, 4, 6)
            end = datetime.date(year + 1, 4, 6)
            total = 0
            while day < end:
                total += stated(day)
                day += datetime.timedelta(days=1)
            values[year] = total / (end - first).days
        else:
            values[year] = stated(datetime.date(year, 4, 30))
    for year, value in values.items():
        leaf.update(period=str(year), value=value)
    return root


def test_future_1436_ordinary_all_dates_and_direct_lookup_share_the_annual_value():
    from policyengine_uk.utils.parameters import convert_to_fiscal_year_parameters

    root = _future_1436_tree()
    leaf = root.gov.future
    convert_to_fiscal_year_parameters(root.gov)
    days = ("01-01", "04-05", "04-06", "04-30", "10-01", "12-31")
    for year, expected in ((2041, 200), (2042, 300)):
        for suffix in (*days, *reversed(days)):
            day = f"{year}-{suffix}"
            assert leaf(day) == expected
            assert root.get_child("gov.future")(day) == expected
            assert root(day).gov.future == expected


@pytest.mark.parametrize("year,after,total", [(2041, 187, 365), (2043, 188, 366)])
def test_future_1436_blend_uses_independent_day_counts(year, after, total):
    from policyengine_uk.utils.parameters import convert_to_fiscal_year_parameters

    root = _future_1436_tree(
        blend=True,
        values={"2010-01-01": 50, f"{year}-04-06": 200, f"{year}-10-01": 300},
    )
    convert_to_fiscal_year_parameters(root.gov)
    expected = (178 * 200 + after * 300) / total
    for suffix in ("12-31", "01-01", "04-06", "10-01"):
        assert root.gov.future(f"{year}-{suffix}") == pytest.approx(expected)
    assert root.gov.future(f"{year + 1}-01-01") == 300


def test_future_1436_sampling_collisions_keep_april30_not_the_last_raw_event():
    from policyengine_uk.utils.parameters import convert_to_fiscal_year_parameters

    root = _future_1436_tree(
        values={
            "2010-01-01": 50,
            "2041-04-05": 120,
            "2041-04-06": 200,
            "2041-04-30": 220,
            "2041-05-01": 230,
            "2041-10-01": 300,
        }
    )
    convert_to_fiscal_year_parameters(root.gov)
    assert root.gov.future("2041-01-01") == 220
    assert root.gov.future("2041-12-31") == 220
    assert root.gov.future("2042-01-01") == 300


def test_future_1436_preserve_calendar_and_non_gov_histories_keep_raw_dates():
    from policyengine_uk.utils.parameters import convert_to_fiscal_year_parameters

    root = _future_1436_tree(preserve=True)
    saved = (root.gov.future.values_list, root.market.values_list)
    convert_to_fiscal_year_parameters(root.gov)
    assert root.gov.future.values_list is saved[0]
    assert root.market.values_list is saved[1]
    for day, expected in (
        ("2041-01-01", 100),
        ("2041-04-06", 200),
        ("2041-10-01", 300),
    ):
        assert root.gov.future(day) == expected
        assert root.market(day) == expected


@pytest.mark.parametrize(
    "value",
    [0, False, None, ["employment_income"]],
    ids=["zero", "false", "null", "list"],
)
def test_future_1436_non_numeric_blend_fallback_preserves_the_exact_value(value):
    from policyengine_uk.utils.parameters import convert_to_fiscal_year_parameters

    root = _future_1436_tree(blend=True, values={"2010-01-01": 11, "2041-04-06": value})
    convert_to_fiscal_year_parameters(root.gov)
    # Numeric zero takes the existing float averaging path; bool False is
    # excluded from that path and retains the exact April30 fallback type.
    expected = 0.0 if type(value) is int else value
    for day in ("2041-01-01", "2041-12-31", "2042-01-01"):
        actual = root.gov.future(day)
        assert actual == expected
        assert type(actual) is type(expected)


def test_future_1436_raw_year_zero_is_preserved_and_keeps_existing_blend_fallback():
    from policyengine_uk.utils.parameters import convert_to_fiscal_year_parameters

    root = _future_1436_tree(
        blend=True,
        values={
            "0000-01-01": 7,
            "2041-04-06": 200,
            "2041-10-01": 300,
        },
    )
    original = root.gov.future.values_list[-1]
    convert_to_fiscal_year_parameters(root.gov)
    assert root.gov.future.values_list[-1] is original
    assert original.instant_str == "0000-01-01"
    assert root.gov.future("2041-01-01") == 200
    assert root.gov.future("2042-01-01") == 300


def test_future_1436_string_values_remain_constructor_errors():
    from policyengine_core.errors import ParameterParsingError
    from policyengine_core.parameters import Parameter

    with pytest.raises(ParameterParsingError):
        Parameter(
            "engineering_string_rejection", data={"2041-04-06": {"value": "not-a-rate"}}
        )


@pytest.mark.parametrize("blend", [False, True], ids=["sample", "blend"])
def test_future_1436_all_26_legacy_export_records_and_leaf_metadata_match_eager_reference(
    blend,
):
    import copy
    from policyengine_uk.utils.parameters import convert_to_fiscal_year_parameters

    actual = _future_1436_tree(
        blend=blend,
        values={
            "2010-01-01": {"value": 50, "metadata": {"note": "retained raw entry"}},
            "2022-04-06": 75,
            "2024-10-30": 100,
            "2041-04-06": 200,
        },
    )
    actual.gov.future.file_path = "engineering-fixture.yaml"
    actual.gov.future.documentation = "Keep leaf documentation and metadata."
    raw_entry = actual.gov.future.values_list[-1]
    metadata = copy.deepcopy(actual.gov.future.metadata)
    reference = _future_1436_eager_reference(actual.clone(), blend)
    convert_to_fiscal_year_parameters(actual.gov)
    observed = [
        row
        for row in _future_1436_records(actual.gov.future)
        if "2015-01-01" <= row[1] < "2041-01-01"
    ]
    expected = [
        row
        for row in _future_1436_records(reference.gov.future)
        if "2015-01-01" <= row[1] < "2041-01-01"
    ]
    assert len(observed) == len(expected) == 26
    assert observed == expected
    assert actual.gov.future.metadata == metadata
    assert actual.gov.future.documentation == reference.gov.future.documentation
    assert actual.gov.future.file_path == reference.gov.future.file_path
    assert actual.gov.future.values_list[-1] is raw_entry


def test_future_1436_conversion_invalidates_views_but_does_not_mutate_clones():
    from policyengine_uk.utils.parameters import convert_to_fiscal_year_parameters

    root = _future_1436_tree()
    baseline = root.clone()
    saved_list = root.gov.future.values_list
    cached = root("2041-01-01")
    assert cached.gov.future == 100
    convert_to_fiscal_year_parameters(root.gov)
    assert root.gov.future.values_list is not saved_list
    assert root("2041-01-01") is not cached
    assert root("2041-01-01").gov.future == 200
    assert baseline.gov.future("2041-01-01") == 100
    baseline.gov.future.update(start="2041-01-01", value=999)
    assert root.gov.future("2041-01-01") == 200


def test_future_1436_scale_brackets_and_ni_aliases_read_the_canonical_history(
    uk_system,
):
    from policyengine_uk.utils.parameters import convert_to_fiscal_year_parameters

    root = uk_system.parameters.clone()
    path = "gov.hmrc.national_insurance.class_1.employee_scale[1].rate"
    canonical = root.get_child(path)
    alias = root.gov.hmrc.national_insurance.class_1.rates.employee.main
    canonical.update(start="2041-01-01", value=0.1)
    canonical.update(start="2041-04-06", value=0.2)
    canonical.update(start="2041-10-01", value=0.3)
    untouched = uk_system.parameters.get_child(path).values_list
    convert_to_fiscal_year_parameters(root.gov.hmrc.national_insurance)
    assert alias.values_list is canonical.values_list
    for day, expected in (
        ("2041-01-01", 0.2),
        ("2041-12-31", 0.2),
        ("2042-01-01", 0.3),
    ):
        assert canonical(day) == expected
        assert alias(day) == expected
        assert root.get_child(path)(day) == expected
        assert (
            root.gov.hmrc.national_insurance.class_1.employee_scale.brackets[1].rate(
                day
            )
            == expected
        )
    assert uk_system.parameters.get_child(path).values_list is untouched


def test_future_1436_representable_ordinary_terminal_year_is_not_arbitrarily_capped():
    from policyengine_uk.utils.parameters import convert_to_fiscal_year_parameters

    root = _future_1436_tree(values={"2010-01-01": 100, "9999-04-30": 200})
    convert_to_fiscal_year_parameters(root.gov)
    assert root.gov.future("9999-01-01") == 200
    assert root.gov.future("9999-12-31") == 200
    assert all(
        not entry.instant_str.startswith("10000")
        for entry in root.gov.future.values_list
    )


@pytest.mark.parametrize(
    "blend,date",
    [(False, "9999-05-01"), (True, "9999-04-06")],
    ids=["next-label-10000", "full-fy-9999"],
)
def test_future_1436_unrepresentable_late_leaf_refuses_before_any_live_tree_change(
    blend, date
):
    import copy
    from policyengine_core.parameters import ParameterNode
    from policyengine_uk.utils.parameters import convert_to_fiscal_year_parameters

    root = _future_1436_tree()
    root.gov.add_child(
        "last_invalid",
        ParameterNode(
            "last_invalid",
            data={
                "value": {
                    "metadata": {"fiscal_year_blend": blend},
                    "values": {"2010-01-01": 50, date: 200},
                }
            },
        ),
    )
    good = root.gov.future
    bad = root.gov.last_invalid.value
    nodes = [root, root.gov, good, root.gov.last_invalid, bad]
    for node in nodes:
        node.modified = False
    cached = root("2020-01-01")
    lists = [leaf.values_list for leaf in (good, bad)]
    records = [_future_1436_records(leaf) for leaf in (good, bad)]
    metadata = [copy.deepcopy(leaf.metadata) for leaf in (good, bad)]
    with pytest.raises(ValueError):
        convert_to_fiscal_year_parameters(root.gov)
    assert all(leaf.values_list is saved for leaf, saved in zip((good, bad), lists))
    assert [_future_1436_records(leaf) for leaf in (good, bad)] == records
    assert [leaf.metadata for leaf in (good, bad)] == metadata
    assert not any(node.modified for node in nodes)
    assert root("2020-01-01") is cached


def test_future_1436_calendar_year_series_metadata_is_not_a_conversion_exemption():
    from policyengine_uk.utils.parameters import convert_to_fiscal_year_parameters

    root = _future_1436_tree()
    root.gov.metadata["calendar_year_series"] = True
    convert_to_fiscal_year_parameters(root.gov)
    assert root.gov.future("2041-01-01") == 200
    assert root.gov.future("2041-10-01") == 200
    assert root.gov.metadata["calendar_year_series"] is True


def test_future_1436_last_complete_gregorian_fiscal_interval_has_a_hand_oracle():
    from policyengine_uk.utils.parameters import fiscal_year_average

    root = _future_1436_tree(
        blend=True,
        values={
            "2010-01-01": 100,
            "9998-04-06": 200,
            "9998-10-01": 300,
        },
    )
    assert fiscal_year_average(root.gov.future, 9998) == pytest.approx(
        (178 * 200 + 187 * 300) / 365
    )
