import pandas as pd
import streamlit as st
import altair as alt
from utils import chart
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress

COMMENT_TEMPLATE_MD = """{} - {}
> {}"""


def space(num_lines=1):
    """Adds empty lines to the Streamlit app."""
    for _ in range(num_lines):
        st.write("")


# data prep

df_1 = pd.read_excel("plantation_fix.xlsx", index_col=[0])
df_1 = df_1.drop(["kind_plantation_business"], axis=1)
df_1["status"] = ["Plantation"] * df_1.shape[0]


df_2 = pd.read_excel("vegetables_fix.xlsx", index_col=[0])
df_2 = df_2.drop(["region"], axis=1)
df_2 = df_2.loc[df_2["commodity"] != "MOLD"]
df_2["status"] = ["Vegetables"] * df_2.shape[0]


padi = pd.read_excel("rice_fix.xlsx", index_col=[0])
padi["commodity"] = ["RICE"] * padi.shape[0]
padi["status"] = ["Rice"] * padi.shape[0]
padi["produksi_tanaman"] = padi["total_productivity"] * 0.1
padi = padi[["commodity", "total_productivity", "unit", "year", "status"]]

df = pd.concat([df_1, df_2, padi])

df_suhu = pd.read_excel("suhu_all.xlsx")
df_suhu["date"] = pd.to_datetime(df_suhu[["year", "month"]].assign(DAY=1))

# aggregrate
data = (
    df[["total_productivity", "year", "commodity", "status"]]
    .groupby(["year", "commodity", "status"], as_index=False)
    .sum()
)

# data buat pie chart
komoditi = data["commodity"].unique()
slope = []
intercept = []
for kom in komoditi:
    potong = data.loc[data["commodity"] == kom]
    a, b, r_value, p_value, std_err = linregress(potong["year"], potong["total_productivity"])
    slope.append(a)
    intercept.append(b)

data_slope = {"commodity": komoditi, "slope": slope, "intercept": intercept}
df_slope = pd.DataFrame(data_slope)

komoditi_naik = df_slope.loc[df_slope["slope"] > 1]["commodity"]
komoditi_turun = df_slope.loc[df_slope["slope"] < -1]["commodity"]
komoditi_tetap = df_slope.loc[(df_slope["slope"] > -1) & (df_slope["slope"] < 1)]["commodity"]


def status(col1):
    if col1 > 1:
        return "komoditi_naik"
    elif col1 < -1:
        return "komoditi_turun"
    else:
        return "komoditi_tetap"


df_slope["status"] = df_slope.apply(lambda x: status(x.slope), axis=1)

# end data prep

# grafik per komoditi
space(2)
st.title("Grafik grafik per komoditi")

option_komoditi = st.selectbox("choose commodity to visualize", data["commodity"].unique())
komoditi_data = data.loc[data["commodity"] == option_komoditi]

min_year = komoditi_data["year"].min()
# st.line_chart(komoditi_data, x="tahun", y="produksi_tanaman")

fig1, ax1 = plt.subplots()
x1 = komoditi_data["year"]
y1 = komoditi_data["total_productivity"]
ax1.plot(x1, y1)
ax1.set_title(f"Graph Production " + option_komoditi.title() + " Commodity")
ax1.set_xlabel("Years")
ax1.set_ylabel("Total Productivity (Ton)")
# sns.lineplot(data=df_suhu_baru, x="Category", y=option_suhu)
st.pyplot(fig1)

# grafik pertahun
space(2)
st.title("Graph each years")

opt1, opt2 = st.columns(2)
with opt1:
    option_status = st.selectbox("choose type commodity", data["status"].unique())
    status_data = data.loc[data["status"] == option_status]
with opt2:
    option_tahun = st.selectbox("choose years", status_data["year"].unique())
    tahun_data = status_data.loc[status_data["year"] == option_tahun]

sort_tahun_data = tahun_data.loc[tahun_data["total_productivity"] > 0].sort_values("total_productivity")

chart_tahun = chart.get_bar_vertical(
    sort_tahun_data,
    "commodity",
    "total_productivity",
    "commodity",
    "Commodity",
    "Total Productivity (Ton)",
    (f"Graph Total Productivity each Commodity in " + str(option_tahun)),
)
st.altair_chart(chart_tahun)

# grafik pie chart
space(2)
st.title("Grafik pie chart")

df_slope_agg = df_slope.groupby(["status"]).count()
label_pie = [
    "production increases",
    "Hasn't Impact",
    "production descrease",
]
fig2, ax2 = plt.subplots()
ax2.pie(df_slope_agg["commodity"], labels=label_pie, autopct="%1.1f%%", startangle=90)
ax2.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.
ax2.set_title("Graph of Percentage Change in Commodity Productivity from 2013 to 2021")
st.pyplot(fig2)

list_komoditi_turun = (
    df_slope.loc[df_slope["status"] == "komoditi_turun"]["commodity"].reset_index().drop(["index"], axis=1)
).rename({"commodity": "commodity decrease"}, axis=1)
list_komoditi_naik = (
    df_slope.loc[df_slope["status"] == "komoditi_naik"]["commodity"].reset_index().drop(["index"], axis=1)
).rename({"commodity": "commodity increase"}, axis=1)
list_komoditi_tetap = (
    df_slope.loc[df_slope["status"] == "komoditi_tetap"]["commodity"].reset_index().drop(["index"], axis=1)
).rename({"commodity": "commodity hasn't impact"}, axis=1)

list_komoditi_turun.index = np.arange(1, len(list_komoditi_turun) + 1)
list_komoditi_naik.index = np.arange(1, len(list_komoditi_naik) + 1)
list_komoditi_tetap.index = np.arange(1, len(list_komoditi_tetap) + 1)


list1, list2, list3 = st.columns(3)
with list1:
    list_komoditi_turun
with list2:
    list_komoditi_naik
with list3:
    list_komoditi_tetap

# suhu
space(2)
st.title("Grafik suhu")

df_suhu_baru = pd.read_csv("temperature_indonesia.csv")
df_suhu_baru_min = df_suhu_baru.loc[df_suhu_baru["Category"] >= min_year]

option_suhu = st.selectbox("Choose Annual Means or 5-yr smooth to visualize", df_suhu_baru_min.columns[1::])

x3 = df_suhu_baru_min["Category"]
y3 = df_suhu_baru_min[option_suhu]

slope, intercept, r_value, p_value, std_err = linregress(x3, y3)

fig3, ax3 = plt.subplots()
ax3.plot(x3, y3)
ax3.set_title("Graph Temperature")
ax3.set_xlabel("Years")
ax3.set_ylabel("Temperature")
ax3.plot(x3, intercept + slope * x3, "r", label="fitted line", linestyle="--")
st.pyplot(fig3)
