"""Build Savings Credit threshold indices from the statutory uprating bases.

The maximum Savings Credit is the phase-in rate multiplied by the difference
between the standard minimum guarantee and the Savings Credit threshold. DWP
uprates the guarantee with earnings and the maximum with CPI. The threshold is
therefore a derived residual; applying CPI to it directly, or freezing it,
does not preserve the statutory relationship. Each generated index is applied
by the standard parameter-uprating operation, so explicit threshold values and
reforms remain authoritative anchors. The indices start from the last year
with enacted rates (pension_age_projection_base.py). The maximum in each
forecast year is the maximum parameter's own projection, so a reform to it,
from any year, reaches the threshold as it did when the threshold was derived
after general uprating.
"""

from decimal import ROUND_HALF_UP, Decimal, localcontext
from sys import float_info
from typing import Any, Iterable

from policyengine_core.parameters import Parameter, ParameterNode
from policyengine_core.parameters.operations.uprate_parameters import (
    get_uprating_dependency_name,
    uprate_parameters,
)

from policyengine_uk.parameters.gov.dwp.pension_credit.pension_age_projection_base import (
    last_enacted_year,
    projection_base_year,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_statutory_uprating_inputs import (
    CPI_OBSERVATION_MONTH_DAY,
)


CURRENCY_PRECISION = Decimal("0.01")


def projection_instant(year: int) -> str:
    """Return the date sampled by fiscal-year parameter conversion."""
    return f"{year}-04-30"


def round_currency(amount: float) -> float:
    """Round a published weekly amount to the nearest penny, halves up."""
    value = Decimal(repr(float(amount)))
    with localcontext() as context:
        context.prec = max(28, value.adjusted() + 4)
        return float(value.quantize(CURRENCY_PRECISION, ROUND_HALF_UP))


def project_maximum_savings_credit(amount: float, cpi_growth: float) -> float:
    """Project maximum Savings Credit without reducing its cash amount."""
    return amount * (1 + max(cpi_growth, 0))


def savings_credit_threshold(
    guarantee: float,
    maximum_savings_credit: float,
    phase_in_rate: float,
) -> float:
    """Solve the statutory maximum-Savings-Credit formula for its threshold."""
    if phase_in_rate <= 0:
        raise ValueError("The Savings Credit phase-in rate must be positive.")
    return guarantee - maximum_savings_credit / phase_in_rate


def _propagated_uprating(parameter: Parameter) -> Any:
    """The uprating metadata a parameter has once metadata is propagated.

    The nearest ancestor that propagates an uprating to its descendants
    overrides the parameter's own (propagate_parameter_metadata).
    """
    node = getattr(parameter, "parent", None)
    while node is not None:
        metadata = node.metadata or {}
        if metadata.get("propagate_metadata_to_children") and "uprating" in metadata:
            return metadata["uprating"]
        node = getattr(node, "parent", None)
    return parameter.metadata.get("uprating")


def _add_at_path(root: ParameterNode, path: str, parameter: Parameter) -> None:
    node = root
    *ancestors, key = path.split(".")
    for name in ancestors:
        if name not in node.children:
            node.add_child(
                name, ParameterNode(name=f"{node.name}.{name}".lstrip("."), data={})
            )
        node = node.children[name]
    node.add_child(key, parameter)


def uprated_values(
    parameter: Parameter, parameters: ParameterNode, years: Iterable[int]
) -> dict[int, float]:
    """A parameter's value in each year once general uprating has run.

    Uprates private copies of the parameter and of each index its uprating
    reads, by Core's own rule, before general uprating has run on the tree.
    Every explicit value, a reform's included, therefore anchors the years
    after it exactly as it will on the parameter itself.
    """
    copies = ParameterNode(data={})
    copied = set()
    path, source = parameter.name, parameter
    # Stop at a repeated path: Core reports the cycle when it uprates.
    while source is not None and path not in copied:
        copied.add(path)
        copy = source.clone()
        uprating = _propagated_uprating(source)
        if uprating is not None:
            copy.metadata["uprating"] = uprating
        _add_at_path(copies, path, copy)
        path = get_uprating_dependency_name(copy)
        source = parameters.get_child(path) if path is not None else None
    uprate_parameters(copies)
    projected = copies.get_child(parameter.name)
    return {year: float(projected(projection_instant(year))) for year in years}


def projected_maximum_values(
    parameters: ParameterNode, relationship: str, base_year: int, final_year: int
) -> dict[int, float]:
    """The maximum Savings Credit in each forecast year, never below zero."""
    maximum = getattr(
        parameters.gov.dwp.pension_credit.savings_credit.maximum, relationship
    )
    years = range(base_year + 1, final_year + 1)
    return {
        year: max(0, value)
        for year, value in uprated_values(maximum, parameters, years).items()
    }


def threshold_index_values(
    base_guarantee: float,
    base_threshold: float,
    phase_in_rate: Parameter,
    earnings_index: Parameter,
    cpi_september: Parameter,
    final_observation_year: int,
    *,
    base_year: int,
    base_maximum: float | None = None,
    price_index: Parameter | None = None,
    maxima: dict[int, float] | None = None,
) -> dict[str, float]:
    """Build a forecast index from the last enacted threshold.

    ``maxima`` gives the maximum Savings Credit in each forecast year. Without
    it, the base maximum is projected by non-negative September CPI.
    """
    base_instant = f"{base_year}-04-01"
    if base_threshold <= 0:
        # The index scales the base, so a reform's zero threshold stays zero.
        return {base_instant: 1.0}
    base_phase_in_rate = float(phase_in_rate(projection_instant(base_year)))
    maximum = (
        max(0, round_currency(base_phase_in_rate * (base_guarantee - base_threshold)))
        if base_maximum is None
        else base_maximum
    )
    base_earnings_index = float(earnings_index(base_instant))
    values = {base_instant: 1.0}

    for year in range(base_year + 1, final_observation_year + 2):
        observation_year = year - 1
        growth = (
            float(price_index(f"{year}-04-01"))
            / float(price_index(f"{year - 1}-04-01"))
            - 1
            if price_index is not None
            else float(cpi_september(f"{observation_year}-{CPI_OBSERVATION_MONTH_DAY}"))
        )
        maximum = (
            maxima[year]
            if maxima is not None
            else project_maximum_savings_credit(maximum, growth)
        )
        guarantee = base_guarantee * (
            float(earnings_index(f"{year}-04-01")) / base_earnings_index
        )
        phase_in = float(phase_in_rate(projection_instant(year)))
        threshold = (
            max(0, savings_credit_threshold(guarantee, maximum, phase_in))
            if phase_in > 0
            else values[f"{year - 1}-04-01"] * base_threshold
        )
        # An exact zero index cannot anchor a later explicit reform (Core
        # divides by the index at that anchor). Keep a positive, finite
        # index even when the non-negative residual reaches zero or the
        # reformed base is subnormal; ordinary monetary bases are unchanged.
        ratio = threshold / base_threshold
        values[f"{year}-04-01"] = min(max(ratio, float_info.min), float_info.max)

    return values


def _projection_parameter(
    relationship: str,
    base_guarantee: float,
    base_threshold: float,
    phase_in_rate: Parameter,
    earnings_index: Parameter,
    cpi_september: Parameter,
    final_observation_year: int,
    base_year: int,
    base_maximum: float,
    price_index: Parameter,
    maxima: dict[int, float] | None = None,
) -> Parameter:
    relationship_label = relationship.lower()
    return Parameter(
        (f"gov.dwp.pension_credit.savings_credit.threshold_uprating.{relationship}"),
        data={
            "description": (
                f"Forecast index for the {relationship_label} Savings Credit "
                "threshold. It derives the threshold from an earnings-projected "
                "standard minimum guarantee and a maximum Savings Credit amount "
                "projected by non-negative September CPI. Explicit threshold "
                "values remain authoritative. Projected values are not enacted "
                "rates."
            ),
            "values": threshold_index_values(
                base_guarantee,
                base_threshold,
                phase_in_rate,
                earnings_index,
                cpi_september,
                final_observation_year,
                base_year=base_year,
                base_maximum=base_maximum,
                price_index=price_index,
                maxima=maxima,
            ),
            "metadata": {
                "unit": "/1",
                "label": (
                    f"Pension Credit Savings Credit {relationship_label} "
                    "threshold forecast index"
                ),
                "reference": [
                    {
                        "title": "State Pension Credit Act 2002 section 3",
                        "href": (
                            "https://www.legislation.gov.uk/ukpga/2002/16/section/3"
                        ),
                    },
                    {
                        "title": (
                            "Social Security Administration Act 1992 section 150"
                        ),
                        "href": (
                            "https://www.legislation.gov.uk/ukpga/1992/5/section/150"
                        ),
                    },
                    {
                        "title": (
                            "Social Security Administration Act 1992 section 150A"
                        ),
                        "href": (
                            "https://www.legislation.gov.uk/ukpga/1992/5/section/150A"
                        ),
                    },
                    {
                        "title": (
                            "Social Security Administration (Northern Ireland) "
                            "Act 1992 section 132"
                        ),
                        "href": (
                            "https://www.legislation.gov.uk/ukpga/1992/8/section/132"
                        ),
                    },
                    {
                        "title": (
                            "Social Security Administration (Northern Ireland) "
                            "Act 1992 section 132A"
                        ),
                        "href": (
                            "https://www.legislation.gov.uk/ukpga/1992/8/section/132A"
                        ),
                    },
                    {
                        "title": (
                            "A14/2025 Housing Benefit uprating for the financial "
                            "year ending March 2027"
                        ),
                        "href": (
                            "https://www.gov.uk/government/publications/"
                            "housing-benefit-adjudication-circulars-2025/"
                            "a142025-housing-benefit-uprating-for-the-financial-"
                            "year-ending-march-2027"
                        ),
                    },
                    {
                        "title": (
                            "ONS KAC3 average weekly earnings, whole economy, total pay"
                        ),
                        "href": (
                            "https://www.ons.gov.uk/employmentandlabourmarket/"
                            "peopleinwork/earningsandworkinghours/timeseries/"
                            "kac3/lms"
                        ),
                    },
                    {
                        "title": "ONS D7G7 Consumer Prices Index annual rate",
                        "href": (
                            "https://www.ons.gov.uk/economy/"
                            "inflationandpriceindices/timeseries/d7g7/mm23"
                        ),
                    },
                ],
            },
        },
    )


def last_projected_year(parameters: ParameterNode) -> int:
    """Last year of main's earnings projection."""
    index = parameters.gov.economic_assumptions.indices.earnings_uprating
    return max(int(entry.instant_str[:4]) for entry in index.values_list)


def enacted_maximum(
    parameters: ParameterNode, relationship: str, base_year: int
) -> float:
    """Use the published maximum; a newer complete rates entry resets its base."""
    pc = parameters.gov.dwp.pension_credit
    maximum = getattr(pc.savings_credit.maximum, relationship)
    if max(int(entry.instant_str[:4]) for entry in maximum.values_list) >= base_year:
        return max(0, float(maximum(projection_instant(base_year))))
    guarantee = getattr(pc.guarantee_credit.minimum_guarantee, relationship)
    threshold = getattr(pc.savings_credit.threshold, relationship)
    at = projection_instant(base_year)
    return max(
        0,
        round_currency(
            float(pc.savings_credit.rate.phase_in(at))
            * (float(guarantee(at)) - float(threshold(at)))
        ),
    )


def project_savings_credit_threshold(
    parameters: ParameterNode,
    unreformed: ParameterNode | None = None,
) -> ParameterNode:
    """Add forecast indices for each Savings Credit threshold.

    The separately set threshold is not re-derived by a guarantee or
    phase-in reform, including a reform to the projection's base year. Use
    the unreformed guarantee unless the corresponding threshold base changes,
    in which case use the reformed pair, and the enacted phase-in rate, so a
    phase-in reform (to zero, say) changes the Savings Credit paid and not the
    threshold. Earnings and CPI inputs come from the reform's tree.

    The maximum Savings Credit is read from the reform's tree as general
    uprating will project it, so a reform to the maximum from the base year
    or any later year moves the projected threshold. A reformed threshold
    base takes precedence: its own reformed gap is projected, as before.
    """
    savings_credit = parameters.gov.dwp.pension_credit.savings_credit
    projection_base = parameters if unreformed is None else unreformed
    base_year = projection_base_year(projection_base)
    base_instant = projection_instant(base_year)
    enacted_savings_credit = projection_base.gov.dwp.pension_credit.savings_credit
    base_thresholds = enacted_savings_credit.threshold
    guarantees = (
        projection_base.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    )
    reformed_guarantees = (
        parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    )
    earnings_index = parameters.gov.economic_assumptions.indices.earnings_uprating
    cpi_september = (
        parameters.gov.economic_assumptions.statutory_uprating_inputs.cpi_september
    )
    projection = ParameterNode(
        name=("gov.dwp.pension_credit.savings_credit.threshold_uprating"),
        data={},
    )
    savings_credit.add_child("threshold_uprating", projection)
    relationship_parameters = {
        "SINGLE": (guarantees.SINGLE, base_thresholds.SINGLE),
        "COUPLE": (guarantees.COUPLE, base_thresholds.COUPLE),
    }
    final_observation_year = last_projected_year(parameters) - 1
    # gov.benefit_uprating_cpi is a YAML alias until parameter propagation.
    # Read its concrete generated September-CPI index at this generation stage.
    price_index = parameters.gov.economic_assumptions.indices.september_cpi_uprating
    for relationship, (
        guarantee_parameter,
        threshold_parameter,
    ) in relationship_parameters.items():
        maximum = enacted_maximum(projection_base, relationship, base_year)
        maximum_parameter = getattr(savings_credit.maximum, relationship)
        enacted_maximum_parameter = getattr(
            enacted_savings_credit.maximum, relationship
        )
        # Enter the maximum a rates update without one implies, but never
        # over a changed maximum timeline, even if its anchors all precede
        # the new base. Entries compare their names, dates and values.
        if (
            last_enacted_year(maximum_parameter) < base_year
            and maximum_parameter.values_list == enacted_maximum_parameter.values_list
        ):
            maximum_parameter.update(start=f"{base_year}-04-01", value=maximum)
        maxima = projected_maximum_values(
            parameters, relationship, base_year, final_observation_year + 1
        )
        reformed_threshold = getattr(savings_credit.threshold, relationship)
        if (
            max(entry.instant_str for entry in reformed_threshold.values_list)
            < base_instant
        ):
            # A pre-base reform can remove the newer enacted anchor. Start
            # its forecast at the common base, where the index is defined.
            reformed_threshold.update(
                start=base_instant, value=reformed_threshold(base_instant)
            )
        if reformed_threshold(base_instant) != threshold_parameter(base_instant):
            threshold_parameter = reformed_threshold
            guarantee_parameter = getattr(reformed_guarantees, relationship)
            maxima = None
            maximum = max(
                0,
                round_currency(
                    float(enacted_savings_credit.rate.phase_in(base_instant))
                    * (
                        float(guarantee_parameter(base_instant))
                        - float(threshold_parameter(base_instant))
                    )
                ),
            )
        projection.add_child(
            relationship,
            _projection_parameter(
                relationship,
                float(guarantee_parameter(base_instant)),
                float(threshold_parameter(base_instant)),
                enacted_savings_credit.rate.phase_in,
                earnings_index,
                cpi_september,
                final_observation_year,
                base_year,
                maximum,
                price_index,
                maxima,
            ),
        )
    return parameters
