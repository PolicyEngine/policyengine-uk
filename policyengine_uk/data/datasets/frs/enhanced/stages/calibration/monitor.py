import streamlit as st
import pandas as pd
import plotly.express as px
import time
from policyengine_uk import REPO

st.header("OpenFisca-UK calibration dashboard")
st.subheader("Inspect training progress by metric and year")

df = pd.read_csv(REPO / "data/storage/training_log_run_1.csv")
df["name_without_year"] = df["name"].apply(
    lambda x: ".".join(x.split(".")[:-1])
)
df["year"] = df.name.str.split(".").str[-1]
df["Predicted"] = df.pred
df["Actual"] = df.actual
df["Error"] = df.pred - df.actual
df["Absolute error"] = (df.pred - df.actual).abs()
df["Relative error"] = (df.pred - df.actual) / df.actual
df["Absolute relative error"] = (df.pred - df.actual).abs() / df.pred
df["Epoch"] = df.epoch

metric = st.selectbox("Metric", df.name.str[:-5].unique())
rerun_every = st.selectbox(
    "Rerun every", ["15 seconds", "minute", "3 minutes", "don't rerun"]
)

subset_df = df[df.name_without_year == metric]


fig_2 = px.line(
    subset_df,
    y="Absolute relative error",
    x="Epoch",
    animation_frame="year",
).update_layout(
    title="Relative error by epoch",
    yaxis_tickformat=".1%",
)

st.write(fig_2)

fig = px.line(
    subset_df,
    y=["Predicted", "Actual"],
    x="Epoch",
    animation_frame="year",
).update_layout(
    title="Outputs by epoch",
)

st.write(fig)

if rerun_every == "15 seconds":
    time.sleep(15)
    st.experimental_rerun()
elif rerun_every == "minute":
    time.sleep(60)
    st.experimental_rerun()
elif rerun_every == "3 minutes":
    time.sleep(180)
    st.experimental_rerun()
else:
    pass
