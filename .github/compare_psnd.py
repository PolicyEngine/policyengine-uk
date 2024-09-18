import pandas as pd

psnd_old = pd.read_csv("psnd_old.csv")
psnd_new = pd.read_csv("psnd_new.csv")

df = pd.DataFrame(
    {
        "year": psnd_old["year"],
        "OBR": psnd_old["OBR"],
        "PE_current": psnd_old["PE"],
        "PE_new": psnd_new["PE"],
    }
)
df["change"] = df["PE_new"] - df["PE_current"]
df["percent_change"] = (df["change"] / df["PE_current"] * 100).round(1)

print("Projection for public sector net debt (PSND):")
print(df.to_markdown(index=False))
