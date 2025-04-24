import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Page configuration
st.set_page_config(
    page_title="Transport Investment Impact Dashboard",
    page_icon="🚊",
    layout="wide"
)

# Title and introduction
st.title("Transportation Investment Impact Analysis")
st.markdown("""
This dashboard explores how investment in public transportation correlates with various outcomes 
across countries, including emissions reduction, efficiency, and economic returns.

Use the sidebar to select countries and metrics of interest. The dashboard provides four main analyses:
1. **Investment vs. Emissions**: How transportation investment relates to environmental outcomes
2. **Investment Trends**: How investment has changed over time across countries
3. **Investment Efficiency**: Which countries get the most benefit per unit of investment
4. **Economic Impact**: How transportation strategies relate to economic outcomes
""")

# Load the data files
@st.cache_data
def load_data():
    transport_wide = pd.read_csv('transport_metrics_agg_wide.csv', index_col='Reference area')
    econ_wide = pd.read_csv('econ_metrics_agg_wide.csv', index_col='Reference area')
    transport_annual = pd.read_csv('transport_metrics_semiwide.csv')
    econ_annual = pd.read_csv('econ_metrics_semiwide.csv')
    combined_metadata = pd.read_csv('combined_measure_metadata.csv')
    yearly_metadata = pd.read_csv('measure_yearly_metadata.csv')
    
    return transport_wide, econ_wide, transport_annual, econ_annual, combined_metadata, yearly_metadata

try:
    transport_wide, econ_wide, transport_annual, econ_annual, combined_metadata, yearly_metadata = load_data()
    st.success("All data loaded successfully!")
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Please make sure all CSV files are present in the app directory.")
    st.stop()

# Display dataset shapes for debugging
if st.checkbox("Show dataset information"):
    st.write("Transport wide data shape:", transport_wide.shape)
    st.write("Economic wide data shape:", econ_wide.shape)
    st.write("Transport annual data shape:", transport_annual.shape)
    st.write("Economic annual data shape:", econ_annual.shape)
    st.write("Combined metadata shape:", combined_metadata.shape)
    st.write("Yearly metadata shape:", yearly_metadata.shape)

# Sidebar with filters
st.sidebar.header("Filters")
selected_countries = st.sidebar.multiselect(
    "Select Countries",
    options=sorted(transport_wide.index.tolist()),
    default=sorted(transport_wide.index.tolist()[:5])  # Default to first 5 countries
)

# Find available investment and CO2 metrics
investment_columns = [col for col in transport_wide.columns if 'Investment' in col and 'pred2000' in col]
co2_columns = [col for col in transport_wide.columns if 'CO2' in col and 'pred2000' in col]

# Create tabs for different analyses
tab1, tab2, tab3, tab4 = st.tabs([
    "Investment vs. Emissions", 
    "Investment Trends", 
    "Investment Efficiency",
    "Economic Impact"
])

# Tab 1: Investment vs Emissions
# Define the specific columns we want to use
x_col = 'Investment (Rail): US dollars per person_pred2000'
y_col = 'CO2 emissions in transport sector: Tonnes of CO2 per person_pred2000'

# Find GDP per capita column in economic data
gdp_cols = [col for col in econ_wide.columns if 'GDP per capita' in col and 'pred2000' in col]
gdp_col = gdp_cols[0] if gdp_cols else None

if not gdp_col:
    st.error("GDP per capita column not found in economic data.")
    st.info("Please make sure economic data contains GDP per capita information.")
    st.stop()

# Merge transport and economic data
data_rows = []
common_countries = set(transport_wide.index) & set(econ_wide.index)

if x_col in transport_wide.columns and y_col in transport_wide.columns and gdp_col in econ_wide.columns:
    for country in common_countries:
        if pd.notna(transport_wide.loc[country, x_col]) and pd.notna(transport_wide.loc[country, y_col]) and pd.notna(econ_wide.loc[country, gdp_col]):
            data_rows.append({
                'Country': country,
                'Rail_Investment': transport_wide.loc[country, x_col],
                'CO2_Emissions': transport_wide.loc[country, y_col],
                'GDP_per_capita': econ_wide.loc[country, gdp_col]
            })
    
    merged_data = pd.DataFrame(data_rows)
else:
    st.error(f"Required columns not found. Looking for {x_col}, {y_col}, and {gdp_col}")
    st.stop()

if merged_data.empty:
    st.error("No valid data found after merging datasets.")
    st.stop()

# Create GDP quartiles
merged_data['GDP_Quartile'] = pd.qcut(merged_data['GDP_per_capita'], 4, labels=['Q1 (Lowest GDP)', 'Q2', 'Q3', 'Q4 (Highest GDP)'])

# Main dashboard
st.header("Investment in Rail Infrastructure vs CO2 Emissions")
st.subheader("Analysis by GDP per Capita Quartiles")

# Create visualization
fig, ax = plt.subplots(figsize=(12, 8))

# Define color palette
palette = sns.color_palette("viridis", 4)

# Plot points colored by GDP quartile
for i, quartile in enumerate(merged_data['GDP_Quartile'].cat.categories):
    quartile_data = merged_data[merged_data['GDP_Quartile'] == quartile]
    sns.scatterplot(
        data=quartile_data,
        x='Rail_Investment',
        y='CO2_Emissions',
        label=quartile,
        color=palette[i],
        s=100,
        ax=ax
    )
    
    # Add country labels
    for _, row in quartile_data.iterrows():
        ax.annotate(
            row['Country'],
            (row['Rail_Investment'], row['CO2_Emissions']),
            fontsize=8,
            alpha=0.7,
            xytext=(5, 5),
            textcoords='offset points'
        )
    
    # Add trendline for each quartile if there are enough points
    if len(quartile_data) >= 3:  # Need at least 3 points for a meaningful trendline
        sns.regplot(
            data=quartile_data,
            x='Rail_Investment',
            y='CO2_Emissions',
            scatter=False,
            color=palette[i],
            line_kws={'linestyle': '--', 'linewidth': 2, 'alpha': 0.7},
            ax=ax
        )

# Calculate overall correlation
correlation = merged_data['Rail_Investment'].corr(merged_data['CO2_Emissions'])

# Add overall trendline
sns.regplot(
    data=merged_data,
    x='Rail_Investment',
    y='CO2_Emissions',
    scatter=False,
    color='red',
    line_kws={'linestyle': '-', 'linewidth': 2},
    ax=ax
)

# Customize the plot
ax.set_xlabel('Investment in Rail (US Dollars per Person)', fontsize=12)
ax.set_ylabel('CO2 Emissions in Transport Sector (Tonnes per Person)', fontsize=12)
ax.set_title('Relationship Between Rail Investment and CO2 Emissions by GDP Quartile', fontsize=14)

# Add correlation text
ax.text(
    0.05, 0.95,
    f'Overall Correlation: {correlation:.2f}',
    transform=ax.transAxes,
    fontsize=12,
    bbox=dict(facecolor='white', alpha=0.7)
)

# Show the legend
ax.legend(title='GDP per Capita Quartile', fontsize=10, title_fontsize=12)

# Add grid for better readability
ax.grid(True, alpha=0.3)

# Show the plot
st.pyplot(fig)

# Add explanation
st.markdown("""
### Insights from the Visualization

This scatter plot reveals the relationship between investment in rail infrastructure and CO2 emissions from the transport sector across countries with different levels of economic development.

**Key observations:**
- Countries are grouped into four quartiles based on GDP per capita (Q1 being lowest, Q4 being highest)
- Each colored trendline shows the relationship within a specific GDP quartile
- The red line represents the overall trend across all countries

**What to look for:**
- Negative slopes indicate that higher rail investment correlates with lower emissions
- Different slopes across GDP quartiles suggest varying investment efficiency
- Outliers may represent countries with unique transportation policies or geographic conditions

**Context:**
Rail infrastructure investment is often considered a strategy for reducing transport emissions by shifting travel from more carbon-intensive modes like personal vehicles to more efficient mass transit.
""")

# Show the data table
st.subheader("Data Table")
st.dataframe(merged_data[['Country', 'Rail_Investment', 'CO2_Emissions', 'GDP_per_capita', 'GDP_Quartile']])