import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- Page Configuration ----------------
st.set_page_config(
    page_title="Groundwater Dashboard",
    layout="wide"
)

st.title("💧 Groundwater Dashboard")
st.markdown("Web-based dashboard for groundwater monitoring and analysis")

# ---------------- Load CSV Data ----------------
@st.cache_data
def load_data():
    # Load Excel file
    file_path = r"D:\python_udemy_haris\PROJECTS\GW_Dashboard\data_odisha\GW_levels_odisha.xlsx"
    # This to be used to upload the file in GIT-HUB
    # file_path = "data_odisha/GW_levels_odisha.xlsx" 
    
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
    # Remove completely empty rows
    df = df.dropna(how="all")

    # Separate inactive wells
    inactive_wells = df[df["Well_Status"] == "Inactive"]

    # Keep only active wells for analysis
    df = df[df["Well_Status"] != "Inactive"]
   
    
    # ---------------- CHECK: Decimal Degree Validation ----------------

    def is_decimal_degree(val):
        try:
            val = float(val)
            return -90 <= val <= 90
        except:
            return False

    def is_decimal_degree_lon(val):
        try:
            val = float(val)
            return -180 <= val <= 180
        except:
            return False

    # Identify problematic rows
    invalid_coords_df = df[
        (~df["Latitude"].apply(is_decimal_degree)) |
        (~df["Longitude"].apply(is_decimal_degree_lon))
    ]

    # Extract problematic Well IDs
    invalid_wells = invalid_coords_df["Well_ID"].unique().tolist()

    print("\n⚠️ Wells with NON-decimal coordinates:\n")
    print(invalid_wells)
    
    # Metadata columns (fixed information)
    meta_cols = [
        "District",
        "Block",
        "Village/Town",
        "Place",
        "Well_Type",
        "Well_ID",
        "Latitude",
        "Longitude",
        "block_ulb" 
    ]

    # Year_Season columns follow YYYY_season pattern
    value_cols = [col for col in df.columns if col not in meta_cols]

    # Convert WIDE → LONG format
    df_long = df.melt(
        id_vars=meta_cols,
        value_vars=value_cols,
        var_name="Year_Season",
        value_name="GWL"
    )
    # It converts GW values into numeric
    df_long["GWL"] = pd.to_numeric(df_long["GWL"], errors="coerce")
   
    # Remove empty groundwater values
    df_long = df_long.dropna(subset=["GWL"])

    # ---------------- Year & Season Extraction ----------------
    # Extract 4-digit year
    df_long["Year"] = df_long["Year_Season"].str.extract(r"(\d{4})")

    # Extract season text AFTER year and underscore
    df_long["Season"] = df_long["Year_Season"].str.extract(r"\d{4}_(.*)")

    # Drop rows where year could not be extracted
    df_long = df_long.dropna(subset=["Year"])

    # Convert Year to integer
    df_long["Year"] = df_long["Year"].astype(int)

    # Clean season names
    df_long["Season"] = df_long["Season"].str.strip()

    # ---------------- Load Rainfall Data ----------------
    rain_path = r"D:\python_udemy_haris\PROJECTS\GW_Dashboard\data_odisha\Rainfall_odisha.xlsx"
    
    # This one to be used to upload on GITHUB
    # rain_path = "data_odisha\Rainfall_odisha.xlsx"

    if rain_path.endswith(".csv"):
        rain_df = pd.read_csv(rain_path)
    else:
        rain_df = pd.read_excel(rain_path)

    # Clean column names
    rain_df.columns = rain_df.columns.str.strip()

    # ---------------- Convert WIDE → LONG ----------------
    rain_cols = [col for col in rain_df.columns if "_Rainfall" in col]

    rain_long = rain_df.melt(
        id_vars=["District"],
        value_vars=rain_cols,
        var_name="Year",
        value_name="Rainfall"
    )

    # Extract year (e.g., 2025_Rainfall → 2025)
    rain_long["Year"] = rain_long["Year"].str.extract(r"(\d{4})")
    rain_long["Year"] = pd.to_numeric(rain_long["Year"], errors="coerce")

    # Clean District names (VERY IMPORTANT)
    rain_long["District"] = (
        rain_long["District"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Convert rainfall to numeric
    rain_long["Rainfall"] = pd.to_numeric(rain_long["Rainfall"], errors="coerce")

    # Remove invalid rows
    rain_long = rain_long.dropna(subset=["Year", "Rainfall"])

    # ---------------- Match Groundwater District Format ----------------
    df_long["District"] = (
        df_long["District"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # ---------------- Merge Rainfall ----------------
    df_long = pd.merge(
        df_long,
        rain_long,
        on=["District", "Year"],
        how="left"
    )

    # return df_long---I have replaced the earlier return df_long command
    return df_long, inactive_wells

# --------call the function-------
# df=load_data()-- I also changed the call function accordingly
df, inactive_wells = load_data()

# st.write(df[["District", "Year", "Rainfall"]].drop_duplicates().head(10)) #temprary code
# print(df.columns.tolist())  # I have turned this into a comment as it is no longer required

# ---------------- Clean block_ulb column ---------------- (block,Block,Ulb,Urban same)
df["block_ulb"] = df["block_ulb"].astype(str).str.strip().str.upper()

# -------------sidebar filters------------------
st.sidebar.header("🔎 Filters")

# ---------------- District Filter (MULTI SELECT) ----------------
district_options = sorted(df["District"].dropna().unique().tolist())

selected_districts = st.sidebar.multiselect(
    "Select District(s)",
    district_options,
    default=district_options   # 👈 All selected by default
)


# ---------------- Block Filter (MULTI BLOCK) ----------------

if selected_districts:
    block_options = sorted(                   # i am making changes everywhere where district filter is used
        df[df["District"].isin(selected_districts)]["Block"]
        .dropna()
        .unique()
    )
else:
    block_options = sorted(df["Block"].dropna().unique())

selected_blocks = st.sidebar.multiselect(
    "Select Block(s)",
    block_options,
    default=block_options
)

# ---------------- Season Filter ----------------
season_filter_df = df.copy()

if selected_districts:
    season_filter_df = season_filter_df[
        season_filter_df["District"].isin(selected_districts)
    ]

# multi select in season filter
if selected_blocks:
    season_filter_df = season_filter_df[
        season_filter_df["Block"].isin(selected_blocks)
    ]

season_options = ["All Seasons"] + sorted(
    season_filter_df["Season"].dropna().unique().tolist()
)

season = st.sidebar.selectbox(
    "Select Season",
    season_options
)

# ---------------- Year Filter (MULTI YEAR) ----------------

year_options = sorted(df["Year"].dropna().unique())

year = st.sidebar.multiselect(
    "Select Year(s)",
    year_options,
    default=year_options
)

# ---------------- Well Type Filter ----------------
well_type_options = ["All Well Types"] + sorted(
    df["Well_Type"].dropna().unique().tolist()
)

well_type = st.sidebar.selectbox(
    "Select Well Type",
    well_type_options
)

# ---------------- Area Type Filter ----------------
area_type_options = ["All", "BLOCK", "ULB"]

area_type = st.sidebar.selectbox(
    "Select Area Type",
    area_type_options
)

# ---------------- Well Filter (DEPENDENT ON DISTRICT & BLOCK) ----------------

# Create a temporary dataframe for well filtering
well_filter_df = df.copy()

# Apply district condition
if selected_districts:
    well_filter_df = well_filter_df[
        well_filter_df["District"].isin(selected_districts)
    ]

# Apply block condition
if selected_blocks:
    well_filter_df = well_filter_df[
        well_filter_df["Block"].isin(selected_blocks)
    ]

# Extract wells only from selected district/block
well_options = sorted(
    well_filter_df["Well_ID"].dropna().unique().tolist()
)

select_all_wells = st.sidebar.checkbox("Select All Wells", value=True)

if select_all_wells:
    selected_wells = well_options
else:
    selected_wells = st.sidebar.multiselect(
        "Select Wells",
        well_options
    )


filtered_df = df.copy()

# District filter
if selected_districts:
    filtered_df = filtered_df[
        filtered_df["District"].isin(selected_districts)
    ]

# Block filter (MULTI BLOCK)
if selected_blocks:
    filtered_df = filtered_df[
        filtered_df["Block"].isin(selected_blocks)
    ]

# Apply season filter
if season != "All Seasons":
    filtered_df = filtered_df[filtered_df["Season"] == season]

# Apply year filter (MULTI YEAR)
if year:
    filtered_df = filtered_df[
        filtered_df["Year"].isin(year)
    ]

# WELL TYPE FILTER
if well_type != "All Well Types":
    filtered_df = filtered_df[
        filtered_df["Well_Type"] == well_type
    ]

# WELL FILTER
filtered_df = filtered_df[
    filtered_df["Well_ID"].isin(selected_wells)
]

# AREA TYPE FILTER
if area_type != "All":
    filtered_df = filtered_df[
        filtered_df["block_ulb"] == area_type
    ]

# ---------------- Menu Navigation ----------------
menu = st.sidebar.radio(
    "Select Dashboard View",
    [
        "Overview",
        "Seasonal Trends",
        "Well Trends",
        "Season Comparison",
        "Block Ranking",
        "Urban vs Block Analysis",
        "Rainfall vs Groundwater",
        "Map View",
        "Inactive Wells",
        "Download Data"
    ]
)

# -----------KPI section---------
if menu == "Overview":

    st.subheader("📊 Key Groundwater Indicators")

    if filtered_df.empty:
        st.warning("No data available for selected filters.")
    else:

        col1, col2, col3, col4, col5 = st.columns(5)

        avg_level = filtered_df["GWL"].mean()
        max_level = filtered_df["GWL"].max()
        min_level = filtered_df["GWL"].min()

        active_wells = df["Well_ID"].nunique()
        inactive_count = inactive_wells["Well_ID"].nunique()

        total_wells = active_wells + inactive_count

        col1.metric("Average Water Level (m bgl)", round(avg_level,2))
        col2.metric("Maximum Depth (m bgl)", round(max_level,2))
        col3.metric("Minimum Depth (m bgl)", round(min_level,2))
        col4.metric("Active Wells", active_wells)
        col5.metric("Inactive Wells", inactive_count)

        st.metric("Total Wells in Monitoring Network", total_wells)
        # ---------------- Annual Groundwater Trend ----------------
        st.subheader("📈 Annual Groundwater Level Trend")

        if filtered_df.empty:
            st.warning("No data available for annual trend.")
        else:

            annual_trend = (
                filtered_df
                .groupby("Year", as_index=False)["GWL"]
                .mean()
            )

            fig_annual = px.line(
                annual_trend,
                x="Year",
                y="GWL",
                markers=True,
                title="Average Annual Groundwater Level",
            )

            fig_annual.update_layout(
                xaxis_title="Year",
                yaxis_title="Average Groundwater Level (m bgl)",
                height=450
            )

            st.plotly_chart(fig_annual, width="stretch")
    st.subheader("⚠️ District-wise Well Status")

    if inactive_wells.empty:
        st.info("No inactive wells found in the dataset.")
    else:

        # Total wells per district
        total_district = (
            pd.concat([df, inactive_wells])
            .groupby("District", as_index=False)["Well_ID"]
            .nunique()
        )

        total_district.rename(
            columns={"Well_ID": "Total Wells"},
            inplace=True
        )

        # Inactive wells per district
        inactive_district = (
            inactive_wells
            .groupby("District", as_index=False)["Well_ID"]
            .nunique()
        )

        inactive_district.rename(
            columns={"Well_ID": "Inactive Wells"},
            inplace=True
        )

        # Merge tables
        district_status = pd.merge(
            total_district,
            inactive_district,
            on="District",
            how="left"
        )

        district_status["Inactive Wells"] = district_status["Inactive Wells"].fillna(0).astype(int)

        district_status = district_status.sort_values(
            "Inactive Wells",
            ascending=False
        )

        st.dataframe(district_status, width="stretch")  



# ---------------- Trend Chart Section ----------------
if menu == "Seasonal Trends":
    st.subheader("📈 Groundwater Level Trend by Season")

    if filtered_df.empty:
        st.warning("No data available for trend analysis.")
    else:
        # Group data by Year & Season (average across wells)
        trend_df = (
            filtered_df
            .groupby(["Year", "Season"], as_index=False)["GWL"]
            .mean()
        )

        fig_trend = px.line(
            trend_df,
            x="Year",
            y="GWL",
            color="Season",
            markers=True,
            title="Season-wise Groundwater Level Trend",
        )

        fig_trend.update_layout(
            xaxis_title="Year",
            yaxis_title="Groundwater Level (m bgl)",
            legend_title="Season",
            height=500
        )

        st.plotly_chart(fig_trend, width="stretch")


# ---------------- Well-wise Trend Chart ----------------
if menu == "Well Trends":
    st.subheader("📈 Well-wise Groundwater Level Trend")

    if filtered_df.empty:
     st.warning("No data available for well-wise trend.")
    else:

     # Ensure numeric groundwater values
        well_trend_df = filtered_df.copy()
        well_trend_df["GWL"] = pd.to_numeric(well_trend_df["GWL"], errors="coerce")

        # Create line chart
        fig_well_trend = px.line(
            well_trend_df,
            x="Year",
            y="GWL",
            color="Well_ID",
            markers=True,
            title="Groundwater Level Trend by Observation Well"
        )

        fig_well_trend.update_layout(
            xaxis_title="Year",
            yaxis_title="Groundwater Level (m bgl)",
            legend_title="Well ID",
            height=500
        )

        st.plotly_chart(fig_well_trend, width="stretch")

    # ---------------- Season Comparison Chart ----------------
if menu == "Season Comparison":
    st.subheader("📊 Seasonal Groundwater Level Comparison")

    if filtered_df.empty:
        st.warning("No data available for seasonal comparison.")
    else:
        # Calculate average GWL for each season
        season_avg = (
            filtered_df
            .groupby("Season", as_index=False)["GWL"]
            .mean()
        )

        # Create bar chart
        fig_season = px.bar(
            season_avg,
            x="Season",
            y="GWL",
            color="Season",
            text_auto=".2f",
            title="Average Groundwater Level by Season"
        )

        fig_season.update_layout(
            xaxis_title="Season",
            yaxis_title="Average Groundwater Level (m bgl)",
            showlegend=False,
            height=450
        )

        st.plotly_chart(fig_season, width="stretch")


# ---------------- Year-wise Extremes (Block vs ULB) ----------------
st.subheader("📅 Year-wise Highest and Lowest Groundwater Levels")

if filtered_df.empty:
    st.warning("No data available for analysis.")
else:

    # Ensure block_ulb is clean
    filtered_df["block_ulb"] = (
        filtered_df["block_ulb"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # ================= BLOCK AREA =================
    block_df = filtered_df[filtered_df["block_ulb"] == "BLOCK"]

    block_results = []

    for year in block_df["Year"].unique():

        temp = block_df[block_df["Year"] == year]

        if not temp.empty:
            highest = temp.loc[temp["GWL"].idxmax()]
            lowest = temp.loc[temp["GWL"].idxmin()]

            block_results.append({
                "Year": year,
                "Highest Block": highest["Block"],
                "Highest GWL (m bgl)": round(highest["GWL"], 2),
                "Lowest Block": lowest["Block"],
                "Lowest GWL (m bgl)": round(lowest["GWL"], 2)
            })

    block_extremes_df = pd.DataFrame(block_results)

    # ================= ULB AREA =================
    ulb_df = filtered_df[filtered_df["block_ulb"] == "ULB"]

    ulb_results = []

    for year in ulb_df["Year"].unique():

        temp = ulb_df[ulb_df["Year"] == year]

        if not temp.empty:
            highest = temp.loc[temp["GWL"].idxmax()]
            lowest = temp.loc[temp["GWL"].idxmin()]

            ulb_results.append({
                "Year": year,
                "Highest Block/ULB": highest["Block"],
                "Highest GWL (m bgl)": round(highest["GWL"], 2),
                "Lowest Block/ULB": lowest["Block"],
                "Lowest GWL (m bgl)": round(lowest["GWL"], 2)
            })

    ulb_extremes_df = pd.DataFrame(ulb_results)

    # ================= DISPLAY =================
    col1, col2 = st.columns(2)

    col1.subheader("🟩 Block Area (Rural)")
    if not block_extremes_df.empty:
        col1.dataframe(block_extremes_df, width="stretch")
    else:
        col1.info("No Block data available")

    col2.subheader("🟥 Urban Area (ULB)")
    if not ulb_extremes_df.empty:
        col2.dataframe(ulb_extremes_df, width="stretch")
    else:
        col2.info("No ULB data available")


# ---------------- Block Ranking Table ----------------
if menu == "Block Ranking":
    st.subheader("🏆 Block Ranking Based on Average Groundwater Level")

    if filtered_df.empty:
        st.warning("No data available for ranking.")
    else:

        block_rank = (
            filtered_df
            .groupby("Block", as_index=False)["GWL"]
            .mean()
        )

        # Rank blocks
        block_rank["Rank (Deepest First)"] = block_rank["GWL"].rank(
            ascending=False,
            method="dense"
        ).astype(int)

        block_rank = block_rank.sort_values("Rank (Deepest First)")

        block_rank.rename(
            columns={"GWL": "Average GWL (m bgl)"},
            inplace=True
        )

        st.dataframe(block_rank, width="stretch")


# ---------------- Urban vs Block Analysis ----------------
if menu == "Urban vs Block Analysis":

    st.subheader("🏙️ Urban vs Block Groundwater Analysis")
    # ---------------- WELL STATUS SUMMARY ----------------
    st.subheader("📊 Well Status Summary: Block vs ULB")

    # Combine active + inactive wells
    all_wells_df = pd.concat([df, inactive_wells], ignore_index=True)

    # Clean block_ulb (important)
    all_wells_df["block_ulb"] = (
        all_wells_df["block_ulb"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # ---------------- Total Wells ----------------
    total_counts = (
        all_wells_df
        .groupby("block_ulb")["Well_ID"]
        .nunique()
    )

    # ---------------- Active Wells ----------------
    active_counts = (
        df
        .groupby("block_ulb")["Well_ID"]
        .nunique()
    )

    # ---------------- Inactive Wells ----------------
    inactive_counts = (
        inactive_wells
        .groupby("block_ulb")["Well_ID"]
        .nunique()
    )

    # ---------------- Display KPIs ----------------
    col1, col2 = st.columns(2)

    # BLOCK
    col1.markdown("### 🟩 Block Area")
    col1.metric("Total Wells", total_counts.get("BLOCK", 0))
    col1.metric("Active Wells", active_counts.get("BLOCK", 0))
    col1.metric("Inactive Wells", inactive_counts.get("BLOCK", 0))

    # ULB
    col2.markdown("### 🟥 Urban (ULB) Area")
    col2.metric("Total Wells", total_counts.get("ULB", 0))
    col2.metric("Active Wells", active_counts.get("ULB", 0))
    col2.metric("Inactive Wells", inactive_counts.get("ULB", 0))
    if filtered_df.empty:
        st.warning("No data available.")
    else:

        # ---------------- Trend Comparison ----------------
        trend_area = (
            filtered_df
            .groupby(["Year", "block_ulb"], as_index=False)["GWL"]
            .mean()
        )

        fig = px.line(
            trend_area,
            x="Year",
            y="GWL",
            color="block_ulb",
            markers=True,
            title="Groundwater Trend: Block vs ULB"
        )

        st.plotly_chart(fig, width="stretch")

        # ---------------- KPIs ----------------
        col1, col2 = st.columns(2)

        block_avg = filtered_df[
            filtered_df["block_ulb"] == "BLOCK"
        ]["GWL"].mean()

        ulb_avg = filtered_df[
            filtered_df["block_ulb"] == "ULB"
        ]["GWL"].mean()

        col1.metric("Block Avg GWL", round(block_avg, 2) if pd.notna(block_avg) else "NA")
        col2.metric("ULB Avg GWL", round(ulb_avg, 2) if pd.notna(ulb_avg) else "NA")

        # ---------------- District-wise Well Status Tables ----------------
        st.subheader("📊 District-wise Well Status (Block vs ULB)")

        # Combine active + inactive wells
        all_wells_df = pd.concat([df, inactive_wells], ignore_index=True)

        # Clean block_ulb
        all_wells_df["block_ulb"] = (
            all_wells_df["block_ulb"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        # ---------------- BLOCK AREA TABLE ----------------
        block_df = all_wells_df[all_wells_df["block_ulb"] == "BLOCK"]

        block_total = (
            block_df
            .groupby("District")["Well_ID"]
            .nunique()
            .reset_index(name="Total Wells")
        )

        block_inactive = (
            inactive_wells[inactive_wells["block_ulb"].str.upper() == "BLOCK"]
            .groupby("District")["Well_ID"]
            .nunique()
            .reset_index(name="Inactive Wells")
        )

        block_status = pd.merge(
            block_total,
            block_inactive,
            on="District",
            how="left"
        )

        block_status["Inactive Wells"] = block_status["Inactive Wells"].fillna(0).astype(int)

        block_status["Inactive %"] = (
            block_status["Inactive Wells"] / block_status["Total Wells"] * 100
        ).round(1)

        block_status = block_status.sort_values("Inactive %", ascending=False)

        # ---------------- ULB AREA TABLE ----------------
        ulb_df = all_wells_df[all_wells_df["block_ulb"] == "ULB"]

        ulb_total = (
            ulb_df
            .groupby("District")["Well_ID"]
            .nunique()
            .reset_index(name="Total Wells")
        )

        ulb_inactive = (
            inactive_wells[inactive_wells["block_ulb"].str.upper() == "ULB"]
            .groupby("District")["Well_ID"]
            .nunique()
            .reset_index(name="Inactive Wells")
        )

        ulb_status = pd.merge(
            ulb_total,
            ulb_inactive,
            on="District",
            how="left"
        )

        ulb_status["Inactive Wells"] = ulb_status["Inactive Wells"].fillna(0).astype(int)

        ulb_status["Inactive %"] = (
            ulb_status["Inactive Wells"] / ulb_status["Total Wells"] * 100
        ).round(1)

        ulb_status = ulb_status.sort_values("Inactive %", ascending=False)

        # ---------------- DISPLAY TABLES ----------------
        col1, col2 = st.columns(2)

        col1.subheader("🟩 Block Area - District Status")
        col1.dataframe(block_status, width="stretch")

        col2.subheader("🟥 ULB Area - District Status")
        col2.dataframe(ulb_status, width="stretch")

        # ---------------- Tables ----------------
        st.subheader("📋 Block Wells")
        st.dataframe(
            filtered_df[filtered_df["block_ulb"] == "BLOCK"],
            width="stretch"
        )

        st.subheader("📋 ULB Wells")
        st.dataframe(
            filtered_df[filtered_df["block_ulb"] == "ULB"],
            width="stretch"
        )

# --------------------Rainfall vs Groundwate Analysis----------------------------
if menu == "Rainfall vs Groundwater":

    st.subheader("🌧️ Rainfall vs Groundwater Analysis")

    if filtered_df.empty:
        st.warning("No data available.")
    else:

        rain_df = filtered_df.copy()

        rain_df["GWL"] = pd.to_numeric(rain_df["GWL"], errors="coerce")
        rain_df["Rainfall"] = pd.to_numeric(rain_df["Rainfall"], errors="coerce")

        rain_df = rain_df.dropna(subset=["GWL", "Rainfall"])

        # Group data
        rain_grouped = (
            rain_df
            .groupby(["Year", "block_ulb"], as_index=False)
            .agg({
                "Rainfall": "mean",
                "GWL": "mean"
            })
        )

        # Scatter plot
        fig = px.scatter(
        rain_grouped,
        x="Rainfall",
        y="GWL",
        color="block_ulb",
        trendline="ols",   # I have installed statsmodels already. So no issues will be created.
        title="Rainfall vs Groundwater Response"
        )

        st.plotly_chart(fig, width="stretch")

        # Correlation
        st.subheader("📊 Correlation")

        corr_block = rain_grouped[
            rain_grouped["block_ulb"] == "BLOCK"
        ][["Rainfall", "GWL"]].corr().iloc[0,1]

        corr_ulb = rain_grouped[
            rain_grouped["block_ulb"] == "ULB"
        ][["Rainfall", "GWL"]].corr().iloc[0,1]

        col1, col2 = st.columns(2)
        col1.metric("Block Correlation", round(corr_block, 2))
        col2.metric("ULB Correlation", round(corr_ulb, 2))

# -------display data table----------
st.subheader("📋 Filtered Groundwater Data")
st.dataframe(filtered_df, width="stretch")


# ---------------- DYNAMIC MAP SECTION ----------------
if menu == "Map View":
    st.subheader("🗺️ Groundwater Observation Wells Map")

    if filtered_df.empty:
        st.warning("No wells to display on map.")
    else:
    #---------------------------- Map Section -------------------------
        map_df = filtered_df.copy()

        # Convert to numeric
        map_df["Latitude"] = pd.to_numeric(map_df["Latitude"], errors="coerce")
        map_df["Longitude"] = pd.to_numeric(map_df["Longitude"], errors="coerce")
        map_df["GWL"] = pd.to_numeric(map_df["GWL"], errors="coerce")

        # Remove invalid rows
        map_df = map_df.dropna(subset=["Latitude", "Longitude", "GWL"])

        # Keep valid coordinate range
        map_df = map_df[
            (map_df["Latitude"].between(-90, 90)) &
            (map_df["Longitude"].between(-180, 180))
        ]

        # Fix size issue
        map_df["GWL_size"] = map_df["GWL"].abs()

        # Clean block_ulb
        map_df["block_ulb"] = (
            map_df["block_ulb"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        if map_df.empty:
            st.warning("No valid coordinates available for mapping.")
        else:
            fig = px.scatter_map(
                map_df,
                lat="Latitude",
                lon="Longitude",
                color="block_ulb",   # 👈 KEY CHANGE
                size="GWL_size",
                hover_data={
                    "District": True,
                    "Block": True,
                    "Well_ID": True,
                    "Season": True,
                    "Year": True,
                    "GWL": True,
                    "block_ulb": True
                },
                color_discrete_map={
                    "BLOCK": "blue",
                    "ULB": "red"
                },
                zoom=6,
                height=500
            )

            st.plotly_chart(fig, width="stretch")
        
        


# ---------------- Inactive Wells Table ----------------
if menu == "Inactive Wells":

    st.subheader("⚠️ Inactive Observation Wells")

    if inactive_wells.empty:
        st.info("No inactive wells found in the dataset.")
    else:
        st.dataframe(
            inactive_wells[
                ["District","Block","Place","Well_ID","Latitude","Longitude"]
            ],
            width="stretch"
        )
# -----Download Button------
if menu == "Download Data":
    st.download_button(
        label="⬇️ Download Filtered Data (CSV)",
        data=filtered_df.to_csv(index=False),
        file_name="filtered_groundwater_data.csv",
        mime="text/csv"
    )