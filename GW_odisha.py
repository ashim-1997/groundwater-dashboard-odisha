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
    # file_path = r"D:\python_udemy_haris\PROJECTS\GW_Dashboard\data_odisha\GW_levels_odisha.xlsx"
    # This to be used to upload the file in GIT-HUB
    file_path = "data_odisha/GW_levels_odisha.xlsx" 
    
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
    
    
    # 🔥 KEEP ORIGINAL COPY (VERY IMPORTANT)
    df_original = df.copy()

    # ---------------- CLEAN WELL STATUS ----------------
    # df["Well_Status"] = (
    #     df["Well_Status"]
    #     .fillna("ACTIVE")   # handle blank values
    #     .astype(str)
    #     .str.strip()
    #     .str.upper()
    # )
    df_original["Well_Status"] = (
    df_original["Well_Status"]
    .fillna("ACTIVE")
    .astype(str)
    .str.strip()
    .str.upper()
    )
    # ---------------- CREATE INACTIVE WELLS ----------------
    inactive_wells = df_original[df_original["Well_Status"] == "INACTIVE"].copy()

    # ---------------- KEEP ONLY ACTIVE FOR ANALYSIS ----------------
    df = df_original[df_original["Well_Status"] != "INACTIVE"].copy()
    
    # Remove completely empty rows
    df = df.dropna(how="all")

    # # Separate inactive wells
    # inactive_wells = df[df["Well_Status"] == "Inactive"]

    # # Keep only active wells for analysis
    # df = df[df["Well_Status"] != "Inactive"]
    # ---------------- CLEAN WELL STATUS FIRST ----------------
    # df["Well_Status"] = df["Well_Status"].astype(str).str.strip().str.upper()

    # ---------------- SEPARATE INACTIVE WELLS ----------------
    # inactive_wells = df[df["Well_Status"] == "INACTIVE"]
    df["Well_Status"] = (
    df["Well_Status"]
    .fillna("ACTIVE")   # 🔥 KEY FIX
    .astype(str)
    .str.strip()
    .str.upper()
    )
    
    # Keep only active wells for analysis
    df = df[df["Well_Status"] != "INACTIVE"]
    
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

    # ---------------- Load Block-wise Rainfall Data ----------------
    # block_rain_path = r"D:\python_udemy_haris\PROJECTS\GW_Dashboard\data_odisha\Rainfall_long_format.xlsx"
    block_rain_path = "Rainfall_long_format.xlsx" # FOR GITHUB UPLOAD

    block_rain_df = pd.read_excel(block_rain_path)

    # Clean column names
    block_rain_df.columns = block_rain_df.columns.str.strip()

    # ---------------- USE LONG FORMAT DIRECTLY ----------------
    rain_long = block_rain_df.copy()

    # Standardize column names (IMPORTANT)
    rain_long.columns = rain_long.columns.str.strip()

    # Ensure correct columns exist
    # Expected: District, Block, Year, Rainfall

    # Convert types
    rain_long["Year"] = pd.to_numeric(rain_long["Year"], errors="coerce")
    rain_long["Rainfall"] = pd.to_numeric(rain_long["Rainfall"], errors="coerce")

    # Clean text
    rain_long["District"] = rain_long["District"].astype(str).str.strip().str.upper()
    rain_long["Block"] = rain_long["Block"].astype(str).str.strip().str.upper()

    # Drop invalid years only
    rain_long = rain_long.dropna(subset=["Year"])

    # Fill missing rainfall (optional but good)
    rain_long["Rainfall"] = rain_long.groupby(
        ["District","Block"]
    )["Rainfall"].transform(lambda x: x.fillna(x.mean()))

    # Convert types
    rain_long["Year"] = pd.to_numeric(rain_long["Year"], errors="coerce")
    rain_long["Rainfall"] = pd.to_numeric(rain_long["Rainfall"], errors="coerce")

    # Clean text columns
    rain_long["District"] = rain_long["District"].astype(str).str.strip().str.upper()
    rain_long["Block"] = rain_long["Block"].astype(str).str.strip().str.upper()

    # Drop missing
    rain_long = rain_long.dropna(subset=["Year"])

    rain_long["Rainfall"] = rain_long.groupby(
        ["District","Block"]
    )["Rainfall"].transform(lambda x: x.fillna(x.mean()))

    # ----------Cleaning the Groundwater Data------------
    df_long["District"] = df_long["District"].astype(str).str.strip().str.upper()
    df_long["Block"] = df_long["Block"].astype(str).str.strip().str.upper()
    
    def clean_text(x):
        x = str(x).upper()
        x = x.replace(".", "")
        x = x.replace("-", " ")
        x = x.replace("BLOCK", "")
        x = x.replace("  ", " ")
        return x.strip()

    # Apply to BOTH datasets
    df_long["District"] = df_long["District"].apply(clean_text)
    rain_long["District"] = rain_long["District"].apply(clean_text)

    df_long["Block"] = df_long["Block"].apply(clean_text)
    rain_long["Block"] = rain_long["Block"].apply(clean_text)

    # Fix known district mismatch
    df_long["District"] = df_long["District"].replace({
        "BALANGIR": "BOLANGIR"
    })
    rain_long["District"] = rain_long["District"].replace({
        "BALANGIR": "BOLANGIR"
    })
    # Ensure Year type matches
    df_long["Year"] = pd.to_numeric(df_long["Year"], errors="coerce")
    rain_long["Year"] = pd.to_numeric(rain_long["Year"], errors="coerce")

    # ---------------- KEEP ALL YEARS (DO NOT DROP RAINFALL) ----------------
    rain_long = rain_long.dropna(subset=["Year"])
    
    # DEBUG BEFORE MERGE
    # st.write("GW District sample:", df_long["District"].unique()[:5])
    # st.write("GW Block sample:", df_long["Block"].unique()[:5])           # THIS PART i CAN USE LATER. SO COMMENT OUT
    # st.write("GW Year sample:", sorted(df_long["Year"].unique())[:5])

    # st.write("Rain District sample:", rain_long["District"].unique()[:5])
    # st.write("Rain Block sample:", rain_long["Block"].unique()[:5])
    # st.write("Rain Year sample:", sorted(rain_long["Year"].unique())[:5])
    
    # Merging the data
    # ---------------- SMART MERGE (BLOCK + ULB FIX) ----------------

    # 🔥 Split data
    df_block = df_long[df_long["block_ulb"].str.upper() == "BLOCK"].copy()
    df_ulb   = df_long[df_long["block_ulb"].str.upper() == "ULB"].copy()

    # ---------------- BLOCK MERGE ----------------
    df_block = pd.merge(
        df_block,
        rain_long,
        on=["District", "Block", "Year"],
        how="left"
    )

    # ---------------- ULB RAINFALL LOGIC ----------------
    # 🔥 Create district-wise rainfall
    district_rain = (
        rain_long
        .groupby(["District", "Year"], as_index=False)["Rainfall"]
        .mean()
    )

    # 🔥 Merge district rainfall to ULB
    df_ulb = pd.merge(
        df_ulb,
        district_rain,
        on=["District", "Year"],
        how="left"
    )

    # 🔥 Ensure same structure
    df_ulb = df_ulb.reindex(columns=df_block.columns)
    
    df_block["Rainfall_Source"] = "Block"
    df_ulb["Rainfall_Source"] = "District Avg"
    
    # ---------------- COMBINE ----------------
    df_long = pd.concat([df_block, df_ulb], ignore_index=True)
    
    # 🔥 ADD AREA TYPE COLUMN (IMPORTANT FOR ANALYSIS)
    df_long["Area_Type"] = df_long["block_ulb"]
    
    
    # ---------------- LAG ANALYSIS ----------------

    # Sort data for correct lag calculation
    df_long = df_long.sort_values(by=["District","Block","Year"])

   
   # ---------------- MULTI-LAG CREATION ----------------

    # ---------------- CORRECT LAG CREATION ----------------

    # Step 1: Create unique block-year rainfall table
    rain_block_year = (
        df_long[["District","Block","Year","Rainfall"]]
        .drop_duplicates()
        .sort_values(by=["District","Block","Year"])
    )

    # Step 2: Create lags correctly (year-wise)
    rain_block_year["Rainfall_Lag0"] = rain_block_year["Rainfall"]

    rain_block_year["Rainfall_Lag1"] = rain_block_year.groupby(
        ["District","Block"]
    )["Rainfall"].shift(1)

    rain_block_year["Rainfall_Lag2"] = rain_block_year.groupby(
        ["District","Block"]
    )["Rainfall"].shift(2)

    # Step 3: Merge back to main dataframe
    df_long = pd.merge(
        df_long,
        rain_block_year[[
            "District","Block","Year",
            "Rainfall_Lag0","Rainfall_Lag1","Rainfall_Lag2"
        ]],
        on=["District","Block","Year"],
        how="left"
)
    # ---------------- GWL CHANGE ----------------

    df_long = df_long.sort_values(by=["District","Block","Well_ID","Year"])

    df_long["GWL_change"] = df_long.groupby(
        ["District","Block","Well_ID"]
    )["GWL"].diff()
    
    # DEBUG AFTER MERGE
    # unmatched = df_long[df_long["Rainfall"].isna()]

    # st.write("Unmatched sample:")
    # st.write(unmatched[["District","Block","Year"]].drop_duplicates().head(20))
    # --------Checking for the umnatched data---------
    missing_blocks = df_long[df_long["Rainfall"].isna()]["Block"].unique()

    # st.write("Unmatched Blocks:", missing_blocks[:20])   
    
    # return df_long---I have replaced the earlier return df_long command
    return df_long, inactive_wells, df_original

# --------call the function-------
# df=load_data()-- I also changed the call function accordingly
df, inactive_wells, df_original = load_data()

# ---------------- MASTER WELL TABLE (IMPORTANT FIX) ----------------
well_master = df_original.drop_duplicates(subset=["Well_ID"]).copy()

well_master["block_ulb"] = well_master["block_ulb"].astype(str).str.strip().str.upper()
well_master["Well_Status"] = well_master["Well_Status"].astype(str).str.strip().str.upper()


st.subheader("🔍 DEBUG: Well Status Distribution")

# debug_master = pd.concat([df, inactive_wells], ignore_index=True) #This needs to be avoided as df is in long format
debug_master = df_original.copy()                                   # which will cause duplicate data creation
st.write(debug_master["Well_Status"].value_counts())
st.write("Total Wells:", debug_master["Well_ID"].nunique())
st.write("Inactive Wells:", debug_master[debug_master["Well_Status"]=="INACTIVE"]["Well_ID"].nunique())
st.write("Total rows:", len(df))
st.write("Rainfall NULL count:", df["Rainfall"].isna().sum())

st.write("Matched rainfall sample:")
st.write(df.dropna(subset=["Rainfall"]).head(10))
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
        "Rainfall Lag Analysis",
        "Best Lag Analysis",
        "GWL Change Analysis",
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
            # 🔥 USE MASTER TABLE (FIX)
        all_wells_df = well_master.copy()

        # Total wells per district
        total_district = (
            all_wells_df
            .groupby("District", as_index=False)["Well_ID"]
            .nunique()
        )

        total_district.rename(
            columns={"Well_ID": "Total Wells"},
            inplace=True
        )

        # Inactive wells per district
        inactive_district = (
            all_wells_df[
                all_wells_df["Well_Status"] == "INACTIVE"
            ]
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

    # ---------------- CLEAN AREA TYPE ----------------
    filtered_df["block_ulb"] = (
        filtered_df["block_ulb"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # ---------------- RURAL (BLOCK) ----------------
    st.subheader("🌾 Block Ranking (Rural Areas)")

    block_df = filtered_df[filtered_df["block_ulb"] == "BLOCK"]

    if block_df.empty:
        st.info("No Block data available.")
    else:
        block_rank = (
            block_df
            .groupby("Block", as_index=False)["GWL"]
            .mean()
        )

        block_rank["Rank"] = block_rank["GWL"].rank(
            ascending=False,
            method="dense"
        ).astype(int)

        block_rank = block_rank.sort_values("Rank")

        block_rank.rename(
            columns={"GWL": "Average GWL (m bgl)"},
            inplace=True
        )

        st.dataframe(block_rank, width="stretch")


    # ---------------- URBAN (ULB) ----------------
    st.subheader("🏙️ ULB Ranking (Urban Areas)")

    ulb_df = filtered_df[filtered_df["block_ulb"] == "ULB"]

    if ulb_df.empty:
        st.info("No ULB data available.")
    else:
        ulb_rank = (
            ulb_df
            .groupby("Block", as_index=False)["GWL"]
            .mean()
        )

        ulb_rank["Rank"] = ulb_rank["GWL"].rank(
            ascending=False,
            method="dense"
        ).astype(int)

        ulb_rank = ulb_rank.sort_values("Rank")

        ulb_rank.rename(
            columns={"GWL": "Average GWL (m bgl)"},
            inplace=True
        )

        st.dataframe(ulb_rank, width="stretch")

        


# # ---------------- MASTER WELL TABLE (IMPORTANT FIX) ----------------
# well_master = df_original.drop_duplicates(subset=["Well_ID"]).copy()

# well_master["block_ulb"] = well_master["block_ulb"].astype(str).str.strip().str.upper()
# well_master["Well_Status"] = well_master["Well_Status"].astype(str).str.strip().str.upper()

# ---------------- Urban vs Block Analysis ----------------
if menu == "Urban vs Block Analysis":

    st.subheader("🏙️ Urban vs Block Groundwater Analysis")
    # ---------------- WELL STATUS SUMMARY ----------------
    st.subheader("📊 Well Status Summary: Block vs ULB")

    # Combine active + inactive wells
    all_wells_df = well_master.copy()

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
    all_wells_df[
        all_wells_df["Well_Status"] != "INACTIVE"
    ]
    .groupby("block_ulb")["Well_ID"]
    .nunique()
    )

    # ---------------- Inactive Wells ----------------
    inactive_counts = (
    all_wells_df[
        all_wells_df["Well_Status"] == "INACTIVE"
    ]
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
        all_wells_df = well_master.copy()

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

        # 🔥 FIXED LOGIC (USE SAME DATAFRAME)

        block_inactive = (
            all_wells_df[
                (all_wells_df["block_ulb"] == "BLOCK") &
                (all_wells_df["Well_Status"].astype(str).str.upper() == "INACTIVE")
            ]
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

        # 🔥 FIXED LOGIC (ULB)

        ulb_inactive = (
            all_wells_df[
                (all_wells_df["block_ulb"] == "ULB") &
                (all_wells_df["Well_Status"].astype(str).str.upper() == "INACTIVE")
            ]
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

# -------------------- Rainfall vs Groundwater Analysis ----------------------------
if menu == "Rainfall vs Groundwater":

    st.subheader("🌧️ Rainfall vs Groundwater Analysis")

    if filtered_df.empty:
        st.warning("No data available.")
    else:

        rain_df = filtered_df.copy()

        # Convert to numeric
        rain_df["GWL"] = pd.to_numeric(rain_df["GWL"], errors="coerce")
        rain_df["Rainfall"] = pd.to_numeric(rain_df["Rainfall"], errors="coerce")

        # Drop missing values
        rain_df = rain_df.dropna(subset=["GWL", "Rainfall"])

        if rain_df.empty:
            st.warning("No rainfall data available after filtering.")
        else:

            # ---------------- GROUP DATA (CORRECT WAY) ----------------
            rain_grouped = (
                rain_df
                .groupby(["Year", "block_ulb"], as_index=False)
                .agg({
                    "Rainfall": "mean",
                    "GWL": "mean"
                })
            )

            # ---------------- SCATTER PLOT ----------------
            fig = px.scatter(
                rain_grouped,
                x="Rainfall",
                y="GWL",
                color="block_ulb",
                title="Rainfall vs Groundwater Response (Block vs ULB)"
            )

            st.plotly_chart(fig, width="stretch")

            # ---------------- CORRELATION ----------------
            st.subheader("📊 Correlation")

            block_data = rain_grouped[rain_grouped["block_ulb"] == "BLOCK"]
            ulb_data = rain_grouped[rain_grouped["block_ulb"] == "ULB"]

            col1, col2 = st.columns(2)

            if not block_data.empty:
                corr_block = block_data[["Rainfall", "GWL"]].corr().iloc[0,1]
                col1.metric("Block Correlation", round(corr_block, 2))
            else:
                col1.metric("Block Correlation", "NA")

            if not ulb_data.empty:
                corr_ulb = ulb_data[["Rainfall", "GWL"]].corr().iloc[0,1]
                col2.metric("ULB Correlation", round(corr_ulb, 2))
            else:
                col2.metric("ULB Correlation", "NA")


# ---------------- Rainfall Lag Analysis ----------------
if menu == "Rainfall Lag Analysis":

    st.subheader("⏳ Rainfall Lag vs Groundwater Analysis")

    lag_df = filtered_df.copy()

    # Convert to numeric
    lag_df["GWL"] = pd.to_numeric(lag_df["GWL"], errors="coerce")
    lag_df["Rainfall_Lag1"] = pd.to_numeric(lag_df["Rainfall_Lag1"], errors="coerce")

    # Drop missing values
    lag_df = lag_df.dropna(subset=["GWL", "Rainfall_Lag1"])

    if lag_df.empty:
        st.warning("No data available for lag analysis.")
    else:

        # Group data
        lag_grouped = (
            lag_df
            .groupby(["Year", "block_ulb"], as_index=False)
            .agg({
                "Rainfall_Lag1": "mean",
                "GWL": "mean"
            })
        )

        # Plot
        fig = px.scatter(
            lag_grouped,
            x="Rainfall_Lag1",
            y="GWL",
            color="block_ulb",
            title="Lagged Rainfall vs Groundwater"
        )

        st.plotly_chart(fig, width="stretch")

        # Correlation
        st.subheader("📊 Lag Correlation")

        corr = lag_grouped[["Rainfall_Lag1","GWL"]].corr().iloc[0,1]

        st.metric("Lag Correlation (1-year)", round(corr, 2))


# ---------------- Block-wise Best Lag Analysis ----------------
if menu == "Best Lag Analysis":

    st.subheader("📊 Block-wise Best Lag Analysis (Urban vs Rural)")

    lag_df = filtered_df.copy()

    # Convert to numeric
    for col in ["GWL", "Rainfall_Lag0", "Rainfall_Lag1", "Rainfall_Lag2"]:
        lag_df[col] = pd.to_numeric(lag_df[col], errors="coerce")

    # Clean area type
    lag_df["block_ulb"] = lag_df["block_ulb"].astype(str).str.upper()

    # ================= BLOCK (RURAL) =================
    st.subheader("🌾 Rural (Block Area)")

    block_df = lag_df[lag_df["block_ulb"] == "BLOCK"]

    block_results = []

    for block in block_df["Block"].unique():

        temp = block_df[block_df["Block"] == block]

        row = {"Block": block}

        for lag in ["Rainfall_Lag0", "Rainfall_Lag1", "Rainfall_Lag2"]:

            temp2 = temp.dropna(subset=["GWL", lag])

            if len(temp2) > 10:
                corr = temp2[[lag, "GWL"]].corr().iloc[0,1]
                row[lag] = round(corr, 3)
            else:
                row[lag] = None

        # Find best lag
        valid = {k:v for k,v in row.items() if k.startswith("Rainfall") and v is not None}

        if valid:
            best_lag = max(valid, key=valid.get)
            row["Best Lag"] = best_lag
        else:
            row["Best Lag"] = None

        block_results.append(row)

    block_result_df = pd.DataFrame(block_results)

    st.dataframe(block_result_df, width="stretch")

    # ================= ULB (URBAN) =================
    st.subheader("🏙️ Urban (ULB Area)")

    ulb_df = lag_df[lag_df["block_ulb"] == "ULB"]

    ulb_results = []

    for block in ulb_df["Block"].unique():

        temp = ulb_df[ulb_df["Block"] == block]

        row = {"Block/ULB": block}

        for lag in ["Rainfall_Lag0", "Rainfall_Lag1", "Rainfall_Lag2"]:

            temp2 = temp.dropna(subset=["GWL", lag])

            if len(temp2) > 10:
                corr = temp2[[lag, "GWL"]].corr().iloc[0,1]
                row[lag] = round(corr, 3)
            else:
                row[lag] = None

        # Best lag
        valid = {k:v for k,v in row.items() if k.startswith("Rainfall") and v is not None}

        if valid:
            best_lag = max(valid, key=valid.get)
            row["Best Lag"] = best_lag
        else:
            row["Best Lag"] = None

        ulb_results.append(row)

    ulb_result_df = pd.DataFrame(ulb_results)

    st.dataframe(ulb_result_df, width="stretch")

# ---------------- GWL Change Analysis ----------------

if menu == "GWL Change Analysis":

    st.subheader("💧 Block-wise Rainfall vs Groundwater Change")

    change_df = filtered_df.copy()

    change_df["GWL_change"] = pd.to_numeric(change_df["GWL_change"], errors="coerce")

    for col in ["Rainfall_Lag0","Rainfall_Lag1","Rainfall_Lag2"]:
        change_df[col] = pd.to_numeric(change_df[col], errors="coerce")

    change_df = change_df.dropna(subset=["GWL_change"])

    change_df["block_ulb"] = change_df["block_ulb"].astype(str).str.upper()

    # ---- RURAL ----
    st.subheader("🌾 Rural")

    rural = change_df[change_df["block_ulb"] == "BLOCK"]

    result = []

    for block in rural["Block"].unique():
        temp = rural[rural["Block"] == block]

        row = {"Block": block}

        for lag in ["Rainfall_Lag0","Rainfall_Lag1","Rainfall_Lag2"]:
            temp2 = temp.dropna(subset=["GWL_change", lag])

            if len(temp2) > 10:
                row[lag] = round(temp2[[lag,"GWL_change"]].corr().iloc[0,1],3)
            else:
                row[lag] = None

        valid = {k:v for k,v in row.items() if v is not None and "Rainfall" in k}

        row["Best Lag"] = max(valid, key=valid.get) if valid else None

        result.append(row)

    df_rural = pd.DataFrame(result)
    
    df_rural = df_rural.sort_values(
        by="Rainfall_Lag1",
        ascending=False,
        na_position="last"
    )

    st.subheader("🏆 Top 5")
    st.dataframe(df_rural.head(5), width="stretch")

    st.subheader("⚠️ Worst 5")
    st.dataframe(df_rural.tail(5), width="stretch")

    st.subheader("📊 Full Table")
    st.dataframe(df_rural, width="stretch")


    # ---- URBAN ----
    st.subheader("🏙️ Urban (ULB)")

    urban = change_df[change_df["block_ulb"] == "ULB"]

    urban_results = []

    for block in urban["Block"].unique():
        temp = urban[urban["Block"] == block]

        row = {"ULB": block}

        for lag in ["Rainfall_Lag0","Rainfall_Lag1","Rainfall_Lag2"]:
            temp2 = temp.dropna(subset=["GWL_change", lag])

            if len(temp2) > 10:
                row[lag] = round(temp2[[lag,"GWL_change"]].corr().iloc[0,1],3)
            else:
                row[lag] = None

        valid = {k:v for k,v in row.items() if v is not None and "Rainfall" in k}

        row["Best Lag"] = max(valid, key=valid.get) if valid else None

        urban_results.append(row)

    df_urban = pd.DataFrame(urban_results)

    # 🔥 SORT
    df_urban = df_urban.sort_values(
        by="Rainfall_Lag1",
        ascending=False,
        na_position="last"
    )

    # 🔝 TOP 5
    st.subheader("🏆 Top 5 (Urban)")
    st.dataframe(df_urban.head(5), width="stretch")

    # 🔻 WORST 5
    st.subheader("⚠️ Worst 5 (Urban)")
    st.dataframe(df_urban.tail(5), width="stretch")

    # 📊 FULL TABLE
    st.subheader("📊 Full Urban Table")
    st.dataframe(df_urban, width="stretch")



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

    # -------display data table----------
    st.subheader("📋 Filtered Groundwater Data")
    st.dataframe(filtered_df, width="stretch")
    