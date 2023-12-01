import pandas as pd
import plotly.express as px
from policyengine_core.charts import format_fig, BLUE, GRAY, DARK_GRAY
import streamlit as st
import numpy as np
from policyengine_uk.system import system
from policyengine_uk import Microsimulation

st.title("PolicyEngine UK calibration dashboard")


training_log_cps = pd.read_csv("calibration_log_cps.csv.gz", compression="gzip")

training_log_cps["Source dataset"] = "Enhanced FRS"

training_log = training_log_cps
training_log_targets = training_log.copy()
training_log_targets["value"] = training_log_targets["target"]
training_log_targets["Source dataset"] = "Official"
training_log = pd.concat([training_log, training_log_targets])

name = st.selectbox(
    "Metric",
    training_log.name.unique(),
)
year = st.selectbox(
    "Year",
    training_log.time_period.unique(),
)

total_loss_log = training_log[(training_log.name == name) & (training_log.time_period == year)]

ground_truth = total_loss_log[total_loss_log["Source dataset"] == "Official"].value.values[0]
last_value = total_loss_log[total_loss_log["Source dataset"] == "Enhanced FRS"].value.values[-1]
relative_error = (last_value - ground_truth) / ground_truth
absolute_error = last_value - ground_truth

column1, column2 = st.columns(2)
with column1:
    st.metric(
        label="Absolute error",
        value=f"{absolute_error:+,.0f}",
    )
with column2:
    st.metric(
        label="Relative error",
        value=f"{relative_error:+.1%}",
    )

last_value_df = training_log[training_log.name == name].groupby(["Source dataset", "time_period"]).last().reset_index()

fig_2 = px.bar(
    last_value_df,
    x="time_period",
    y="value",
    color="Source dataset",
    barmode="group",
    color_discrete_map={
        "Enhanced FRS": BLUE,
        "Official": DARK_GRAY,
    },
)

fig_2 = format_fig(fig_2).update_layout(
    title=f"{name} after reweighting, by source dataset",
    yaxis_title="Relative loss change",
    xaxis_title="Year",
    legend_title="",
    yaxis_range=[0, 1.5 * max(last_value_df.value)],
)

fig_2

fig = px.line(
    total_loss_log,
    x="epoch",
    y="value",
    color="Source dataset",
    color_discrete_map={
        "Enhanced FRS": BLUE,
        "Official": DARK_GRAY,
    },
)


fig = format_fig(fig)
fig.update_layout(
    title=f"{name} during reweighting, by source dataset",
    yaxis_title="Relative loss change",
    xaxis_title="Epoch",
    legend_title="",
    yaxis_range=[0, 1.5 * max(total_loss_log.value)],
)
fig


last_value_df = training_log.groupby(["Source dataset", "time_period", "name"]).last().reset_index()


show_full_table = st.checkbox("Show full table")
if show_full_table:
    comparison_df = pd.DataFrame({
        "Official": last_value_df[last_value_df["Source dataset"] == "Official"].value.values,
        "Enhanced FRS": last_value_df[last_value_df["Source dataset"] == "Enhanced FRS"].value.values,
        "Year": last_value_df[last_value_df["Source dataset"] == "Official"].time_period.values,
        "Metric": last_value_df[last_value_df["Source dataset"] == "Official"].name.values,
    })
    comparison_df["Relative error"] = (comparison_df["Enhanced FRS"] - comparison_df["Official"]) / comparison_df["Official"]
    comparison_df["Absolute error"] = comparison_df["Enhanced FRS"] - comparison_df["Official"]
    st.write(comparison_df.sort_values("Relative error"))

sim = Microsimulation(dataset="calibrated_frs_2019_21")

with st.expander("See variable aggregates"):
    chosen_variable = st.selectbox(
        "Variable",
        system.variables.keys(),
    )
    aggregates = []
    for year in range(2023, 2028):
        aggregates += [sim.calculate(chosen_variable, period=year).sum()]
    
    fig = px.bar(
        pd.DataFrame({
            "Year": range(2023, 2028),
            "Aggregate": aggregates,
        }),
        x="Year",
        y="Aggregate",
    )
    fig.update_layout(
        title=f"Aggregate {chosen_variable} over time",
        xaxis_title="Year",
        yaxis_title="Aggregate",
    )
    st.write(fig)
