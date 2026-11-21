from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# Page setup
st.set_page_config(
    page_title="Used Car Price Explorer",
    page_icon="🚘",
    layout="wide",
)


st.title("🚘 Used Car Price Explorer")
st.caption(
    "Explore used-car listings and see how prices vary with the car's "
    "fuel, year, transmission, and kilometres driven."
)

# Find the project folder and load the cleaned data
project_folder = Path(__file__).resolve().parent.parent
csv_path = project_folder / "data" / "processed" / "cleaned_car_data.csv"

if not csv_path.exists():
    st.error(
        "Cleaned data not found. Run the Jupyter notebook and save "
        "cleaned_car_data.csv in data/processed/."
    )
    st.stop()

cars = pd.read_csv(csv_path)

# Check that the main dashboard columns exist
required_columns = [
    "name", "year", "selling_price", "km_driven", "fuel",
    "transmission", "owner"
]
missing_columns = [column for column in required_columns if column not in cars.columns]

if missing_columns:
    st.error(f"The cleaned file is missing these columns: {missing_columns}")
    st.stop()

# Ensure values used in filters and charts are numeric
for column in ["year", "selling_price", "km_driven"]:
    cars[column] = pd.to_numeric(cars[column], errors="coerce")

cars = cars.dropna(subset=["year", "selling_price", "km_driven"])

if cars.empty:
    st.error("There are no usable car records in the cleaned CSV.")
    st.stop()

# Sidebar filters
st.sidebar.title("Filter listings")
st.sidebar.caption("Choose options to explore the cars.")

fuel_options = ["All"] + sorted(cars["fuel"].dropna().astype(str).unique())
selected_fuel = st.sidebar.selectbox(
    "Fuel type", fuel_options, key="fuel_filter_v2"
)

transmission_options = ["All"] + sorted(
    cars["transmission"].dropna().astype(str).unique()
)
selected_transmission = st.sidebar.selectbox(
    "Transmission", transmission_options, key="transmission_filter_v2"
)

owner_options = ["All"] + sorted(cars["owner"].dropna().astype(str).unique())
selected_owner = st.sidebar.selectbox(
    "Owner history", owner_options, key="owner_filter_v2"
)

year_min = int(cars["year"].min())
year_max = int(cars["year"].max())
selected_years = st.sidebar.slider(
    "Model year",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max),
    key="year_range_filter_v2",
)

price_min = int(cars["selling_price"].min())
price_max = int(cars["selling_price"].max())
selected_prices = st.sidebar.slider(
    "Selling price range (₹)",
    min_value=price_min,
    max_value=price_max,
    value=(price_min, price_max),
    step=10000,
    format="₹%d",
    key="price_range_filter_v2",
)
# Apply the selected filters
filtered_cars = cars.copy()

if selected_fuel != "All":
    filtered_cars = filtered_cars[filtered_cars["fuel"] == selected_fuel]

if selected_transmission != "All":
    filtered_cars = filtered_cars[
        filtered_cars["transmission"] == selected_transmission
    ]

if selected_owner != "All":
    filtered_cars = filtered_cars[filtered_cars["owner"] == selected_owner]

filtered_cars = filtered_cars[
    filtered_cars["year"].between(selected_years[0], selected_years[1])
    & filtered_cars["selling_price"].between(
        selected_prices[0], selected_prices[1]
    )
]
if filtered_cars.empty:
    st.info("No cars match those filters. Try widening your selections.")
    st.stop()

# Summary cards
st.subheader("At a glance")
metric_one, metric_two, metric_three, metric_four = st.columns(4)
metric_one.metric("Cars in view", f"{len(filtered_cars):,}")
metric_two.metric(
    "Average price",
    f"₹{filtered_cars['selling_price'].mean():,.0f}",
)
metric_three.metric(
    "Median price",
    f"₹{filtered_cars['selling_price'].median():,.0f}",
)
metric_four.metric(
    "Average kilometres",
    f"{filtered_cars['km_driven'].mean():,.0f} km",
)

# Organize the dashboard into three easy sections
overview_tab, explore_tab, quality_tab = st.tabs(
    ["Overview", "Explore prices", "Data quality"]
)

with overview_tab:
    left_chart, right_chart = st.columns(2)

    with left_chart:
        st.subheader("Median price by fuel type")
        median_by_fuel = filtered_cars.groupby("fuel")["selling_price"].median()
        st.bar_chart(median_by_fuel)

    with right_chart:
        st.subheader("Listings by car make")
        filtered_cars["make"] = filtered_cars["name"].str.split().str[0]
        top_makes = filtered_cars["make"].value_counts().head(10)
        st.bar_chart(top_makes)

    st.subheader("Average price by model year")
    average_by_year = (
        filtered_cars.groupby("year")["selling_price"].mean().sort_index()
    )
    st.line_chart(average_by_year)

with explore_tab:
    st.subheader("Price versus kilometres driven")
    st.scatter_chart(
        filtered_cars,
        x="km_driven",
        y="selling_price",
        color="fuel",
    )
    st.caption("Each point is a car listing. Selling prices are in Indian rupees.")

    st.subheader("Selling price distribution")
    figure, axis = plt.subplots(figsize=(9, 4))
    axis.hist(filtered_cars["selling_price"], bins=25, color="#2384a8")
    axis.set_xlabel("Selling price (₹)")
    axis.set_ylabel("Number of cars")
    axis.set_title("How asking prices are distributed")
    st.pyplot(figure)
    plt.close(figure)

with quality_tab:
    st.subheader("Missing values in the filtered data")
    missing_counts = filtered_cars.isna().sum()
    missing_counts = missing_counts[missing_counts > 0].sort_values(ascending=False)

    if missing_counts.empty:
        st.success("No missing values in the filtered records.")
    else:
        st.bar_chart(missing_counts)
        st.caption("These are missing values remaining in the cleaned dataset.")

    st.subheader("Filtered car records")
    st.dataframe(filtered_cars, use_container_width=True)

st.caption("Use the filters on the left to update the summary and charts.")

