import streamlit as st
import pandas as pd
from microdf import MicroDataFrame
import numpy as np
import plotly.express as px
from policyengine_core.charts import format_fig, BLUE, BLUE_LIGHT
from Home import STYLE

# st.set_page_config(layout="wide")

st.write(STYLE, unsafe_allow_html=True)
st.title("Capital Gains Tax")

st.markdown(
    """This page documents PolicyEngine's in-progress capital gains imputations in the PolicyEngine UK microsimulation model."""
)

st.subheader("Method")

st.markdown(
    """Our input data consists of: PolicyEngine's Enhanced FRS (incorporating WAS, LCFS, SPI and ONS/OBR summary data), and joint capital gains-taxable income data from [CAGE working paper no. 465, *Capital Gains and UK Inequality* (Arun Advani, Andy Summers)](https://warwick.ac.uk/fac/soc/economics/research/centres/cage/manage/publications/wp465.2020.pdf).
         
This data includes p05, p10, p25, p50, p75, p90, and p95 percentiles of capital gains (given gains != 0) as well as the percentage with gains for each of over 60 income bands. We fit a spline to each income band's percentiles, and use these splines to impute capital gains for each individual in the microsimulation model as an initial approach.

The below figure is interactive and shows the fitted spline for each income band.
         """
)

st.warning(
    "**Caveat:** so far, we've only used income bands up to over £128,000, so won't capture the very highest earners."
)

capital_gains = pd.read_csv("../capital_gains_distribution.csv")
capital_gains["maximum_total_income"] = (
    capital_gains.minimum_total_income.shift(-1).fillna(np.inf)
)
# Fit a spline to each income band's percentiles
from scipy.interpolate import UnivariateSpline

splines = {}

for i in range(len(capital_gains)):
    row = capital_gains.iloc[i]
    splines[row.minimum_total_income] = UnivariateSpline(
        [0.05, 0.1, 0.25, 0.5, 0.75, 0.90, 0.95],
        [row.p05, row.p10, row.p25, row.p50, row.p75, row.p90, row.p95],
        k=2,
    )

with st.expander("Capital gains-income joint distribution input data"):
    st.dataframe(capital_gains)

with st.expander("Capital gains-income joint distribution fitted splines"):
    income_band = st.select_slider(
        "Income band",
        capital_gains.minimum_total_income,
        format_func=lambda x: f"£{x:,.0f}",
    )

    fig = (
        px.line(
            x=np.linspace(0, 1, 100),
            y=splines[income_band](np.linspace(0, 1, 100)),
        )
        .update_layout(
            title="Percentiles of capital gains",
            yaxis_title="Capital gains",
            xaxis_title="Percentile",
            yaxis_tickformat=",.0f",
            yaxis_tickprefix="£",
            xaxis_tickformat=".0%",
            yaxis_range=[capital_gains.p05.min(), capital_gains.p95.max()],
        )
        .update_traces(line=dict(color=BLUE))
    )

    st.plotly_chart(format_fig(fig), use_container_width=True)

from tqdm import tqdm
from policyengine_uk.system import system

cgt_revenue = system.parameters.calibration.programs.capital_gains.total

lower_income_bounds = list(splines)
uprating_from_2017 = cgt_revenue("2023-01-01") / cgt_revenue("2017-01-01")


def impute_capital_gains(total_income: float) -> float:
    if total_income < 0:
        return 0
    distribution_row = capital_gains[
        (capital_gains["minimum_total_income"] <= total_income)
        & (capital_gains["maximum_total_income"] > total_income)
    ]
    percent_with_gains = distribution_row["percent_with_gains"].values[0]
    has_gains = np.random.choice(
        [0, 1], p=[1 - percent_with_gains, percent_with_gains]
    )
    if not has_gains:
        return 0
    for i in range(len(splines)):
        if lower_income_bounds[i] > total_income:
            continue
    i -= 1
    sample_percentile = np.random.random()
    spline = splines[lower_income_bounds[i]]
    return spline(sample_percentile) * uprating_from_2017


imputed_gains = []

st.markdown(
    """Then, for every household in the model, we randomly sample their probability of gains according to the capital gains statistics, and sample a random quantile from the relevant income band's fitted spline to determine the amount if they are imputed to have gains. You can run this process on individual income data inputs below."""
)

with st.expander("Capital gains imputation test runner"):

    income = st.slider("Total income", 0, 500000, 50000, 1000)

    with st.spinner("Imputing capital gains..."):
        capital_gains = [impute_capital_gains(income) for _ in range(100)]

    fig = (
        px.histogram(x=capital_gains, nbins=10)
        .update_layout(
            title="Imputed capital gains",
            xaxis_title="Capital gains",
            yaxis_title="Frequency",
            xaxis_tickformat=",.0f",
            xaxis_tickprefix="£",
            xaxis_range=[0, 1_000_000],
        )
        .update_traces(marker=dict(color=BLUE))
    )

    st.plotly_chart(format_fig(fig), use_container_width=True)

st.subheader("Analysis")

st.markdown(
    """We can use the imputed capital gains to analyse the distribution of capital gains in the model. The below figure shows the joint distribution of total income and capital gains as a scatter plot."""
)

st.warning("**Again**- in progress.")


@st.cache_resource
def get_microsimulation():
    from policyengine_uk import Microsimulation

    sim = Microsimulation()
    sim.calculate("household_net_income")
    return sim


sim = get_microsimulation()

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Total capital gains",
        f"£{sim.calculate('capital_gains').sum()/1e9:.1f}bn",
    )

with col2:
    st.metric(
        "Total CGT revenue",
        f"£{sim.calculate('capital_gains_tax').sum()/1e9:.1f}bn",
    )


with st.expander("PolicyEngine UK capital gains-income joint distribution"):
    fig = (
        px.scatter(
            x=sim.calculate("total_income"),
            y=sim.calculate("capital_gains"),
            opacity=0.1,
        )
        .update_traces(line=dict(color=BLUE))
        .update_layout(
            title="PolicyEngine UK capital gains-income joint distribution",
            xaxis_title="Total income",
            yaxis_title="Capital gains",
            xaxis_tickformat=",.0f",
            xaxis_tickprefix="£",
            yaxis_tickformat=",.0f",
            yaxis_tickprefix="£",
        )
    )

    st.plotly_chart(format_fig(fig), use_container_width=True)
