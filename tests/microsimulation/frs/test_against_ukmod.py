"""
This module tests the microsimulation outputs produced by openfisca-uk-data against UKMOD - checking that the distributions are similar.
"""

from openfisca_uk.analytics.ukmod_benchmarking import benchmark_against_UKMOD
import pytest
import logging

df = benchmark_against_UKMOD()


@pytest.mark.parametrize(
    "variable,metric",
    zip(df.variable, df.metric),
)
def test_distribution_parameter_close_to_UKMOD(variable, metric):
    index = df[df.variable == variable][df.metric == metric].index.values[0]
    results = dict(df.loc[index])
    assert (results["abs_err"] < 10) or (
        results["rel_err"] < results["max_rel_err"]
    )
