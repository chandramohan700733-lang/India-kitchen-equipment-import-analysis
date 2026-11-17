"""
Step 1: Clean the UN Comtrade extract (India imports of HS 841981, 2015-2025).

Source : UN Comtrade (comtradeplus.un.org), downloaded 11 Nov 2026
Query  : Reporter = India, Flow = Import, HS 841981, Partner = all, Annual
Output : data/clean/imports_clean.csv, data/clean/world_totals.csv, hattori.db
"""
import sqlite3
import numpy as np
import pandas as pd

RAW = "data/raw/comtrade_india_import_841981_2015_2025.csv"

df = pd.read_csv(RAW)

# 1) Keep only the columns we need, with readable names
cols = {
    "refYear": "year",
    "partnerCode": "partner_code",
    "partnerISO": "partner_iso",
    "partnerDesc": "partner",
    "classificationCode": "hs_version",
    "primaryValue": "value_usd",
    "qty": "qty_units",
    "isQtyEstimated": "qty_estimated",
    "netWgt": "net_wgt_kg",
    "isNetWgtEstimated": "wgt_estimated",
    "isReported": "is_reported",
}
df = df[list(cols)].rename(columns=cols)

# 2) Basic quality checks
assert df["year"].between(2015, 2025).all()
assert not df.duplicated(["year", "partner_code"]).any(), "duplicate year/partner rows"
print("Rows:", len(df), "| Years:", df.year.min(), "-", df.year.max())
print("Missing values:\n", df[["value_usd", "qty_units", "net_wgt_kg"]].isna().sum())

# 3) Split the 'World' total row (partner_code 0) from the country rows
world = df[df.partner_code == 0].copy()
countries = df[df.partner_code != 0].copy()

# 4) Check: do country rows add up to the World total? (avoids double counting)
chk = (countries.groupby("year").value_usd.sum()
       .to_frame("sum_partners").join(world.set_index("year").value_usd.rename("world")))
chk["diff_usd"] = chk.sum_partners - chk.world
print("\nSum of partners vs World total:\n", chk.round(0))
assert chk.diff_usd.abs().max() < 10, "partners do not add up to World"

# 5) Flag partners that are not real countries
NON_COUNTRY = {"Areas, nes", "Other Asia, nes", "Antarctica"}
countries["partner_type"] = np.where(countries.partner.isin(NON_COUNTRY), "Not specified", "Country")
countries.loc[countries.partner == "India", "partner_type"] = "Re-import (India)"

# 6) Derived metrics (only where the denominator is valid)
# FINDING: every net-weight value in this extract is flagged as ESTIMATED by the UN
# (it is derived from the trade value), so $/kg would just reflect that estimate.
# We therefore do NOT use weight for price analysis. Quantity (units) is reported, so we use it.
print("\nRows with estimated net weight:", int(countries.wgt_estimated.sum()), "of", len(countries))
countries["usd_per_unit"] = np.where(countries.qty_units > 0, countries.value_usd / countries.qty_units, np.nan)
countries = countries.drop(columns=["net_wgt_kg"])

# 7) Market share per year
totals = countries.groupby("year").value_usd.transform("sum")
countries["share_pct"] = countries.value_usd / totals * 100

# 8) Save
countries.sort_values(["year", "value_usd"], ascending=[True, False]).to_csv("data/clean/imports_clean.csv", index=False)
world[["year", "value_usd", "qty_units", "hs_version"]].sort_values("year").to_csv("data/clean/world_totals.csv", index=False)

with sqlite3.connect("hattori.db") as con:
    countries.to_sql("imports_clean", con, if_exists="replace", index=False)
    world.to_sql("world_totals", con, if_exists="replace", index=False)
print("\nSaved: data/clean/imports_clean.csv, data/clean/world_totals.csv, hattori.db")
