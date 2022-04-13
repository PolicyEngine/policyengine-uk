import pandas as pd
import calendar

# Download ONS monthly inflation by COICOP category from https://www.ons.gov.uk/filter-outputs/7bd1b688-29f5-47c4-9f0d-c43a22708d12

df = pd.read_csv(
    "~/Downloads/cpih01-time-series-v20-filtered-2022-04-12T12-30-35Z.csv"
)

month_to_code = {
    month: index for index, month in enumerate(calendar.month_abbr) if month
}

df["month_code"] = df["mmm-yy"].apply(lambda x: month_to_code[x.split("-")[0]])
df["year"] = df["mmm-yy"].apply(lambda x: x.split("-")[1]).astype(int)
df["date_str"] = [
    f"{2000 + year if year < 30 else 1900 + year}-{month:02}-01"
    for month, year in zip(df.month_code, df.year)
]

CATEGORY_RENAMES = {
    1: "food_and_non_alcoholic_beverages",
    2: "alcohol_and_tobacco",
    3: "clothing_and_footwear",
    4: "housing_water_and_electricity",
    5: "household_furnishings",
    6: "health",
    7: "transport",
    8: "communication",
    9: "recreation",
    10: "education",
    11: "restaurants_and_hotels",
    12: "miscellaneous",
}

df["category"] = df.Aggregate.apply(
    lambda x: CATEGORY_RENAMES[int(x.split(" ")[0])]
)

df["value"] = df.v4_0

param = ""

for category in CATEGORY_RENAMES.values():
    param += f"\n\n{category}:\n"
    subset = df[df.category == category].sort_values("date_str")
    for date_str, value in zip(subset.date_str, subset.value):
        param += f"  {date_str}: {value:.02f}\n"

print(param)
