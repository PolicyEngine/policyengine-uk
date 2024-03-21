import pandas as pd
import plotly.express as px
from policyengine_core.charts import *
import streamlit as st
import numpy as np
from policyengine_uk.data.storage import STORAGE_FOLDER

st.set_page_config(layout="wide")

st.title("PolicyEngine UK microdata dashboard")

df = pd.read_csv(STORAGE_FOLDER / "dataset_losses.csv.gz")

df.dataset = df.dataset.replace(
    {
        "frs_2021": "FRS (2021)",
        "enhanced_frs": "Enhanced FRS",
    }
)

df["rel_error"] = df.value / df.target - 1
df["abs_rel_error"] = (df.value / df.target - 1).abs()

st.dataframe(df[df.dataset == "Enhanced FRS"], use_container_width=True)

left, right = st.columns(2)
with left:
    metric = st.selectbox("Metric", df.name.unique())
with right:
    time_period = st.selectbox("Time period", df.time_period.unique())


def capitalise(string):
    return string[0].upper() + string[1:]

df["Text"] = df.rel_error.apply(lambda x: f"{x:+.0%}")

fig = px.bar(
    df[(df.name == metric) & (df.time_period == time_period)],
    x="dataset",
    y="value",
    color="dataset",
    title=f"{capitalise(metric)} in {time_period}",
    color_discrete_sequence=[MEDIUM_DARK_GRAY, BLUE],
    text="Text",
).update_layout(
    yaxis_title="Absolute relative error",
    xaxis_title="Dataset",
    showlegend=False,
)

# Add dotted line for truth

true_value = df[
    (df.name == metric) & (df.time_period == time_period)
].target.mean()
fig.add_shape(
    type="line",
    x0=-0.5,
    y0=true_value,
    x1=len(df.dataset.unique()) - 0.5,
    y1=true_value,
    line=dict(
        color=MEDIUM_DARK_GRAY,
        width=3,
        dash="dash",
    ),
)

st.plotly_chart(fig, use_container_width=True)

quantiles = []
datasets = []
values = []

for quantile in np.linspace(0.1, 0.9, 9):
    for dataset in df.dataset.unique():
        datasets.append(dataset)
        quantiles.append(quantile)
        values.append(df[df.dataset == dataset][df.time_period == time_period].abs_rel_error.quantile(quantile))

quantile_df = pd.DataFrame({"Dataset": datasets, "Quantile": quantiles, "Value": values})
quantile_df["Text"] = quantile_df.Value.apply(lambda x: f"{x:.0%}")

fig = px.bar(
    quantile_df,
    y="Value",
    x="Quantile",
    text="Text",
    color="Dataset",
    title="Quantiles of absolute relative error, by dataset",
    labels={"Dataset": "Dataset", "Quantile": "Quantile"},
    barmode="group",
    color_discrete_sequence=[MEDIUM_DARK_GRAY, BLUE],
)

st.plotly_chart(fig, use_container_width=True)