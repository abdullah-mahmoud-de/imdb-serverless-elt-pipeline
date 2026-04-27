import streamlit as st

# ---------------------------------------------------------
# 1. Page Configuration & Connection
# ---------------------------------------------------------
st.set_page_config(page_title="Movie Explorer", page_icon="❄️", layout="wide")
conn = st.connection("snowflake")

# ---------------------------------------------------------
# 2. Global Sidebar Filters
# ---------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/2/28/Snowflake_Logo.svg", width=150)
st.sidebar.header("🎯 Global Filters")

# Year Range Slider
min_year, max_year = st.sidebar.slider(
    "Release Year Range",
    min_value=1890,
    max_value=2026,
    value=(1990, 2026) # Default selection
)

# Genre Multiselect (Hardcoded popular genres to keep the UI lightning fast)
popular_genres = [
    "Action", "Adventure", "Animation", "Comedy", "Documentary", 
    "Drama", "Horror", "Romance", "Sci-Fi", "Thriller"
]
selected_genres = st.sidebar.multiselect("Filter by Genre", popular_genres)

# ---------------------------------------------------------
# 3. Dynamic SQL Construction
# ---------------------------------------------------------
# We build a base WHERE clause that updates based on the sidebar
base_where = f"WHERE release_year BETWEEN {min_year} AND {max_year}"

if selected_genres:
    # If they select genres, we dynamically add ILIKE conditions for each
    # Example: AND (genres ILIKE '%Action%' OR genres ILIKE '%Comedy%')
    genre_conditions = " OR ".join([f"genres ILIKE '%{g}%'" for g in selected_genres])
    base_where += f" AND ({genre_conditions})"

# ---------------------------------------------------------
# 4. Main Dashboard UI
# ---------------------------------------------------------
st.title("❄️ Movie Insights Explorer")
st.markdown("Interact with the sidebar to filter the entire database in real-time.")

# --- Quick Stats (KPIs) ---
st.markdown("### 📊 Quick Stats")
kpi1, kpi2, kpi3 = st.columns(3)

# Notice how we inject {base_where} into the query
kpi_query = f"""
    SELECT 
        COUNT(*) AS "Total", 
        ROUND(AVG(runtime_mins)) AS "Avg_Runtime",
        MAX(release_year) AS "Newest"
    FROM v_clean_movies
    {base_where};
"""
kpi_df = conn.query(kpi_query, ttl=600)

if not kpi_df.empty:
    kpi1.metric("Total Movies Tracked", f"{kpi_df['Total'][0]:,}")
    # Handle potential None values if filters are too strict
    avg_run = kpi_df['Avg_Runtime'][0]
    kpi2.metric("Average Runtime", f"{avg_run} mins" if avg_run else "N/A")
    kpi3.metric("Latest Release", int(kpi_df['Newest'][0]) if kpi_df['Newest'][0] else "N/A")

st.markdown("---")

# --- CHART 1: Trend Over Time ---
st.markdown("### 📈 Movies Released Over Time")
trend_query = f"""
    SELECT release_year AS "Year", COUNT(*) AS "Total Movies"
    FROM v_clean_movies
    {base_where}
    GROUP BY release_year
    ORDER BY release_year;
"""
trend_df = conn.query(trend_query, ttl=600)
if not trend_df.empty:
    st.line_chart(trend_df, x="Year", y="Total Movies", use_container_width=True)

# Create columns for the next charts
col1, col2 = st.columns(2)

# --- CHART 2: Runtime Distribution ---
with col1:
    st.markdown("### ⏱️ Runtime Distribution")
    # We use 'AND' here because 'base_where' already starts with 'WHERE'
    runtime_query = f"""
        SELECT FLOOR(runtime_mins / 10) * 10 AS "Runtime (Minutes)", COUNT(*) AS "Total Movies"
        FROM v_clean_movies
        {base_where} AND runtime_mins IS NOT NULL AND runtime_mins > 0 AND runtime_mins <= 300
        GROUP BY 1
        ORDER BY 1;
    """
    runtime_df = conn.query(runtime_query, ttl=600)
    if not runtime_df.empty:
        st.bar_chart(runtime_df, x="Runtime (Minutes)", y="Total Movies", use_container_width=True)

# --- CHART 3: Top Genres ---
with col2:
    st.markdown("### 🎭 Top 10 Genres")
    genre_query = f"""
        SELECT TRIM(f.value::STRING) AS "Genre", COUNT(*) AS "Total Movies"
        FROM v_clean_movies, LATERAL FLATTEN(INPUT => SPLIT(genres, ',')) f
        {base_where} AND genres IS NOT NULL AND genres != '\\N'
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 10;
    """
    genre_df = conn.query(genre_query, ttl=600)
    if not genre_df.empty:
        st.bar_chart(genre_df, x="Genre", y="Total Movies", use_container_width=True)

# --- CHART 4: Top Regions ---
st.markdown("---")
st.markdown("### 🌍 Top 10 Production Regions")

region_query = f"""
    SELECT 
        TRIM(f.value::STRING) AS "Region Code", 
        COUNT(*) AS "Total Movies"
    FROM v_clean_movies, 
    LATERAL FLATTEN(INPUT => SPLIT(available_regions, ',')) f
    {base_where} AND available_regions != 'Unknown' AND available_regions IS NOT NULL
    GROUP BY 1
    ORDER BY 2 DESC
    LIMIT 10;
"""
region_df = conn.query(region_query, ttl=600)

if not region_df.empty:
    st.bar_chart(
        region_df,
        x="Region Code",
        y="Total Movies",
        use_container_width=True
    )

# ---------------------------------------------------------
# 5. The Raw Data Expander
# ---------------------------------------------------------
st.markdown("---")
# This keeps the massive data table neatly tucked away until the user clicks it
with st.expander("🔎 View & Search Raw Data"):
    search_term = st.text_input("Search by exact Movie Title:", placeholder="e.g., The Matrix")
    
    if search_term:
        table_query = f"""
            SELECT title, release_year, runtime_mins, genres, available_regions
            FROM v_clean_movies
            {base_where} AND title ILIKE :1
            ORDER BY release_year DESC
            LIMIT 100;
        """
        table_df = conn.query(table_query, params=[f"%{search_term}%"], ttl=600)
    else:
        table_query = f"""
            SELECT title, release_year, runtime_mins, genres, available_regions
            FROM v_clean_movies
            {base_where}
            ORDER BY release_year DESC
            LIMIT 100;
        """
        table_df = conn.query(table_query, ttl=600)
        
    st.dataframe(table_df, use_container_width=True, hide_index=True)