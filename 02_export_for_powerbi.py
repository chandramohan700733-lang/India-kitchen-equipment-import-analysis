"""
Step 2: Build the small summary tables that Power BI will use.
Run after 01_clean.py.
"""
import sqlite3
import pandas as pd

con = sqlite3.connect("hattori.db")
countries = pd.read_sql("SELECT * FROM imports_clean WHERE partner_type = 'Country'", con)

# Yearly total + growth
yearly = (countries.groupby("year", as_index=False).value_usd.sum()
          .assign(value_musd=lambda d: d.value_usd / 1e6))
yearly["yoy_pct"] = yearly.value_usd.pct_change() * 100
yearly.to_csv("data/clean/yearly_totals.csv", index=False)

# Top suppliers per year (top 10) plus "Others"
top = countries.sort_values(["year", "value_usd"], ascending=[True, False]).groupby("year").head(10)
top.to_csv("data/clean/top_suppliers.csv", index=False)

# Focus group: Japan vs top suppliers over time
focus = countries[countries.partner.isin(["Japan", "China", "Italy", "Germany", "USA"])]
focus.to_csv("data/clean/japan_vs_top.csv", index=False)

# CAGR 2015-2025 for the total market
n = 2025 - 2015
cagr = (yearly.value_usd.iloc[-1] / yearly.value_usd.iloc[0]) ** (1 / n) - 1
print(f"Market CAGR 2015-2025: {cagr:.1%}")
print("Saved: yearly_totals.csv, top_suppliers.csv, japan_vs_top.csv")
