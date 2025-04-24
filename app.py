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
# Calculate GDP quartiles
gdp_col = "Gross domestic product (GDP) (Total): US dollars/capita_pred2000"
countries_with_gdp = []

# Make sure we only include countries present in both datasets
for country in transport_wide.index:
    if country in econ_wide.index and pd.notna(econ_wide.loc[country, gdp_col]):
        countries_with_gdp.append({
            'Country': country,
            'GDP_per_capita': econ_wide.loc[country, gdp_col]
        })

gdp_data = pd.DataFrame(countries_with_gdp)
gdp_data['GDP_Quartile'] = pd.qcut(
    gdp_data['GDP_per_capita'], 
    4, 
    labels=['Q1 (Lowest GDP)', 'Q2', 'Q3', 'Q4 (Highest GDP)']
)

# Create country lists by quartile
q1_countries = sorted(gdp_data[gdp_data['GDP_Quartile'] == 'Q1 (Lowest GDP)']['Country'].tolist())
q2_countries = sorted(gdp_data[gdp_data['GDP_Quartile'] == 'Q2']['Country'].tolist())
q3_countries = sorted(gdp_data[gdp_data['GDP_Quartile'] == 'Q3']['Country'].tolist())
q4_countries = sorted(gdp_data[gdp_data['GDP_Quartile'] == 'Q4 (Highest GDP)']['Country'].tolist())

# Create a dictionary for countries without GDP data (if any)
countries_without_gdp = sorted(list(set(transport_wide.index) - set(gdp_data['Country'])))

# Sidebar with filters by GDP quartile
st.sidebar.header("Countries by GDP Per Capita")

# Create expandable sections for each quartile
with st.sidebar.expander("Q1 - Lowest GDP Countries", expanded=True):
    selected_q1 = st.multiselect(
        "Select Q1 Countries",
        options=q1_countries,
        default=q1_countries[:2] if len(q1_countries) >= 2 else q1_countries
    )

with st.sidebar.expander("Q2 - Lower-Middle GDP Countries", expanded=True):
    selected_q2 = st.multiselect(
        "Select Q2 Countries",
        options=q2_countries,
        default=q2_countries[:2] if len(q2_countries) >= 2 else q2_countries
    )

with st.sidebar.expander("Q3 - Upper-Middle GDP Countries", expanded=True):
    selected_q3 = st.multiselect(
        "Select Q3 Countries",
        options=q3_countries,
        default=q3_countries[:2] if len(q3_countries) >= 2 else q3_countries
    )

with st.sidebar.expander("Q4 - Highest GDP Countries", expanded=True):
    selected_q4 = st.multiselect(
        "Select Q4 Countries",
        options=q4_countries,
        default=q4_countries[:2] if len(q4_countries) >= 2 else q4_countries
    )

# Section for countries without GDP data (if any)
if countries_without_gdp:
    with st.sidebar.expander("Countries with Unknown GDP", expanded=False):
        selected_unknown = st.multiselect(
            "Select Countries",
            options=countries_without_gdp,
            default=[]
        )
    # Combine selections from all quartiles plus unknown GDP countries
    selected_countries = selected_q1 + selected_q2 + selected_q3 + selected_q4 + selected_unknown
else:
    # Combine selections from all quartiles
    selected_countries = selected_q1 + selected_q2 + selected_q3 + selected_q4

# Show the total number of selected countries
st.sidebar.write(f"**Total countries selected:** {len(selected_countries)}")

# Optional: Display GDP quartile ranges
if st.sidebar.checkbox("Show GDP quartile ranges"):
    quartile_ranges = gdp_data.groupby('GDP_Quartile')['GDP_per_capita'].agg(['min', 'max'])
    st.sidebar.dataframe(quartile_ranges.style.format("${:,.0f}"))

# Find available investment and CO2 metrics
investment_columns = [col for col in transport_wide.columns if 'Investment' in col and 'pred2000' in col]
co2_columns = [col for col in transport_wide.columns if 'CO2' in col and 'pred2000' in col]

# Create tabs for different analyses
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Investment vs. Emissions", 
    "Investment Trends", 
    "Investment Efficiency",
    "Economic Impact",
    "Custom metrics"
])

# Tab 1: Investment vs Emissions
with tab1:
    st.header("Public Transport Investment vs CO2 Emissions")

# Metric selection
col1, col2 = st.columns(2)
with col1:
    selected_investment = st.selectbox(
        "Select Investment Metric",
        options=investment_columns,
        index=0 if investment_columns else 0
    )
    
with col2:
    selected_co2 = st.selectbox(
        "Select CO2 Emission Metric",
        options=co2_columns,
        index=0 if co2_columns else 0
    )

# Create the scatter plot
if investment_columns and co2_columns:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot all countries as background
    sns.scatterplot(
        x=transport_wide[selected_investment],
        y=transport_wide[selected_co2],
        alpha=0.3,
        color='gray',
        ax=ax
    )
    
    # Highlight selected countries
    if selected_countries:
        selected_data = transport_wide.loc[selected_countries]
        sns.scatterplot(
            x=selected_data[selected_investment],
            y=selected_data[selected_co2],
            ax=ax,
            s=100,
            hue=selected_data.index
        )
    
        # Add annotations for selected countries
        for country in selected_countries:
            if country in transport_wide.index:
                x = transport_wide.loc[country, selected_investment]
                y = transport_wide.loc[country, selected_co2]
                ax.annotate(country, (x, y), xytext=(5, 5), textcoords='offset points')
    
    # Add regression line
    sns.regplot(
        x=transport_wide[selected_investment],
        y=transport_wide[selected_co2],
        scatter=False,
        ax=ax,
        color='red',
        line_kws={'linestyle': '--'}
    )
    
    # Clean up the column names for the axis labels
    x_label = selected_investment.split('_pred2000')[0]
    y_label = selected_co2.split('_pred2000')[0]
    
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(f'Relationship between {x_label} and {y_label}')
    
    # Add quadrant lines to divide plot into 4 regions (using medians)
    x_median = transport_wide[selected_investment].median()
    y_median = transport_wide[selected_co2].median()
    
    ax.axvline(x=x_median, color='gray', linestyle=':', alpha=0.5)
    ax.axhline(y=y_median, color='gray', linestyle=':', alpha=0.5)
    
    # Add quadrant labels
    ax.text(
        transport_wide[selected_investment].max() * 0.9,
        transport_wide[selected_co2].min() * 1.1,
        "High Investment\nLow Emissions",
        ha='right',
        bbox=dict(facecolor='green', alpha=0.1)
    )
    
    ax.text(
        transport_wide[selected_investment].min() * 1.1,
        transport_wide[selected_co2].max() * 0.9,
        "Low Investment\nHigh Emissions",
        ha='left',
        bbox=dict(facecolor='red', alpha=0.1)
    )
    
    st.pyplot(fig)
    
    # Add explanation
    st.markdown("""
    **Interpretation:**
    - **Top Left**: Countries with low investment but high emissions
    - **Top Right**: Countries with high investment and high emissions
    - **Bottom Left**: Countries with low investment and low emissions
    - **Bottom Right**: Countries with high investment and low emissions (typically most desirable)
    
    The regression line shows the general relationship between investment and emissions across all countries.
    """)
    
    # Show the data in a table
    if selected_countries:
        st.subheader("Data for Selected Countries")
        selected_data = transport_wide.loc[selected_countries, [selected_investment, selected_co2]]
        selected_data.columns = [x_label, y_label]
        st.dataframe(selected_data)
else:
    st.warning("No investment or CO2 metrics found in the data.")

# Tab 2: Investment vs Fatalities
with tab2:
    st.header("Road Investment vs Traffic Fatalities")
    
    # Get investment columns from transport_wide data
    road_investment_columns = [col for col in transport_wide.columns if 'Investment' in col and 'Road' in col and 'pred2000' in col]
    fatality_columns = [col for col in transport_wide.columns if 'Fatalities' in col and 'inhabitants' in col and 'pred2000' in col]
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_road_inv = st.selectbox(
            "Select Road Investment Metric",
            options=road_investment_columns,
            index=0 if road_investment_columns else 0
        )
    
    with col2:
        selected_fatality = st.selectbox(
            "Select Fatality Metric",
            options=fatality_columns,
            index=0 if fatality_columns else 0
        )
    
    if selected_road_inv and selected_fatality:
        # Create the scatter plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot all countries as background
        sns.scatterplot(
            x=transport_wide[selected_road_inv],
            y=transport_wide[selected_fatality],
            alpha=0.3,
            color='gray',
            ax=ax
        )
        
        # Highlight selected countries
        if selected_countries:
            selected_data = transport_wide.loc[selected_countries]
            selected_data = selected_data.dropna(subset=[selected_road_inv, selected_fatality])
            
            # Only proceed if we have valid data
            if not selected_data.empty:
                # Get GDP data for selected countries if available
                for country in selected_data.index:
                    if country in gdp_data['Country'].values:
                        selected_data.loc[country, 'GDP_Quartile'] = gdp_data.loc[gdp_data['Country'] == country, 'GDP_Quartile'].values[0]
                    else:
                        selected_data.loc[country, 'GDP_Quartile'] = 'Unknown'
                
                # Plot with color by GDP quartile if available
                if 'GDP_Quartile' in selected_data.columns:
                    sns.scatterplot(
                        data=selected_data,
                        x=selected_road_inv,
                        y=selected_fatality,
                        hue='GDP_Quartile',
                        palette='viridis',
                        s=100,
                        ax=ax
                    )
                else:
                    # Fallback if no GDP data
                    sns.scatterplot(
                        data=selected_data,
                        x=selected_road_inv,
                        y=selected_fatality,
                        hue=selected_data.index,
                        s=100,
                        ax=ax
                    )
                
                # Add annotations for selected countries
                for country in selected_data.index:
                    x = selected_data.loc[country, selected_road_inv]
                    y = selected_data.loc[country, selected_fatality]
                    ax.annotate(country, (x, y), xytext=(5, 5), textcoords='offset points')
        
        # Add regression line
        valid_data = transport_wide.dropna(subset=[selected_road_inv, selected_fatality])
        if len(valid_data) >= 3:  # Need at least 3 points for regression
            sns.regplot(
                x=valid_data[selected_road_inv],
                y=valid_data[selected_fatality],
                scatter=False,
                ax=ax,
                color='red',
                line_kws={'linestyle': '--'}
            )
        
        # Clean up the column names for the axis labels
        x_label = selected_road_inv.split('_pred2000')[0]
        y_label = selected_fatality.split('_pred2000')[0]
        
        ax.set_xlabel(x_label, fontsize=11)
        ax.set_ylabel(y_label, fontsize=11)
        ax.set_title(f'Relationship between Road Investment and Traffic Fatalities', fontsize=14)
        
        # Add quadrant lines (using medians)
        x_median = transport_wide[selected_road_inv].median()
        y_median = transport_wide[selected_fatality].median()
        
        ax.axvline(x=x_median, color='gray', linestyle=':', alpha=0.5)
        ax.axhline(y=y_median, color='gray', linestyle=':', alpha=0.5)
        
        # Add quadrant labels
        ax.text(
            transport_wide[selected_road_inv].max() * 0.9,
            transport_wide[selected_fatality].min() * 1.1,
            "High Investment\nLow Fatalities",
            ha='right',
            bbox=dict(facecolor='green', alpha=0.1)
        )
        
        ax.text(
            transport_wide[selected_road_inv].min() * 1.1,
            transport_wide[selected_fatality].max() * 0.9,
            "Low Investment\nHigh Fatalities",
            ha='left',
            bbox=dict(facecolor='red', alpha=0.1)
        )
        
        # Calculate and display correlation
        if len(valid_data) >= 3:
            correlation = valid_data[selected_road_inv].corr(valid_data[selected_fatality])
            ax.text(
                0.05, 0.95,
                f'Correlation: {correlation:.2f}',
                transform=ax.transAxes,
                fontsize=10,
                bbox=dict(facecolor='white', alpha=0.7)
            )
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3)
        
        # Show the plot
        st.pyplot(fig)
        
        # Add explanation
        st.markdown("""
        **Investment in Road Infrastructure vs Traffic Fatalities**
        
        This visualization examines the relationship between road infrastructure investment and traffic safety outcomes.
        
        **Interpretation:**
        - Road transit is typically the most hazardous. We explore whether investment in roads will mitigate this or exacerbate it. 
        - Points in the lower right quadrant (high investment, low fatalities) represent countries that have effectively invested in road safety
        - Points in the upper left quadrant (low investment, high fatalities) may indicate underinvestment in road safety
        - The correlation coefficient measures the strength of the relationship between road investment and fatality rates
        - A negative correlation suggests that higher road investment is associated with fewer traffic fatalities
        
        Different countries may have different approaches to road safety, including infrastructure design, traffic laws, 
        enforcement, and driver education programs. These factors, combined with investment levels, influence fatality rates.
        """)
        
        # Show the data table
        if selected_countries:
            st.subheader("Data for Selected Countries")
            display_data = selected_data[[selected_road_inv, selected_fatality]].copy()
            display_data.columns = [x_label, y_label]
            st.dataframe(display_data)
    else:
        st.warning("Please select both road investment and fatality metrics for the analysis.")


# Tab 3: Investment Efficiency with Rail Network and Transit Cost
# Tab 3: Employment in Transport Sector by GDP Quartile
with tab3:
    st.header("Employment in Transport Sector by Economic Development Level")
    
    # Find the employment in transport sector column
    employment_cols = [col for col in transport_wide.columns 
                       if "Employment in the transport sector" in col and "pred2000" in col]
    
    if employment_cols:
        # Select an employment metric
        selected_employment = st.selectbox(
            "Select Employment Metric",
            options=employment_cols,
            index=0 if employment_cols else 0
        )
        
        # Create GDP quartiles dataframe
        gdp_col = "Gross domestic product (GDP) (Total): US dollars/capita_pred2000"
        
        if gdp_col in econ_wide.columns:
            # Create a dataframe with countries, GDP, and employment data
            data_rows = []
            
            for country in transport_wide.index:
                if pd.notna(transport_wide.loc[country, selected_employment]) and country in econ_wide.index:
                    if pd.notna(econ_wide.loc[country, gdp_col]):
                        data_rows.append({
                            'Country': country,
                            'GDP_per_capita': econ_wide.loc[country, gdp_col],
                            'Employment': transport_wide.loc[country, selected_employment]
                        })
            
            if data_rows:
                employment_data = pd.DataFrame(data_rows)
                
                # Create GDP quartiles
                employment_data['GDP_Quartile'] = pd.qcut(
                    employment_data['GDP_per_capita'], 
                    4, 
                    labels=['Q1 (Lowest GDP)', 'Q2', 'Q3', 'Q4 (Highest GDP)']
                )
                
                # Filter to selected countries if any are selected
                if selected_countries:
                    filtered_data = employment_data[employment_data['Country'].isin(selected_countries)]
                    if filtered_data.empty:
                        st.warning("None of the selected countries have both GDP and employment data.")
                        # Use all countries with data as a fallback
                        filtered_data = employment_data
                else:
                    # Use all countries with data
                    filtered_data = employment_data
                
                # Create the boxplot
                fig, ax = plt.subplots(figsize=(12, 8))
                
                # Generate the boxplot
                sns.boxplot(
                    data=filtered_data,
                    x='GDP_Quartile',
                    y='Employment',
                    ax=ax,
                    palette='viridis'
                )
                
                # Add individual data points as a swarm plot
                sns.swarmplot(
                    data=filtered_data,
                    x='GDP_Quartile',
                    y='Employment',
                    color='black',
                    alpha=0.7,
                    ax=ax
                )
                
                # Add country labels to points
                for idx, row in filtered_data.iterrows():
                    ax.annotate(
                        row['Country'],
                        (row['GDP_Quartile'], row['Employment']),
                        xytext=(5, 0),
                        textcoords='offset points',
                        fontsize=8,
                        alpha=0.7
                    )
                
                # Customize the plot
                employment_label = selected_employment.split('_pred2000')[0]
                ax.set_xlabel('GDP per Capita Quartile', fontsize=12)
                ax.set_ylabel(employment_label, fontsize=12)
                ax.set_title('Employment in Transport Sector by GDP Quartile', fontsize=14)
                ax.grid(True, axis='y', alpha=0.3)
                
                # Calculate quartile statistics
                quartile_stats = filtered_data.groupby('GDP_Quartile')['Employment'].agg(['mean', 'median', 'std', 'count'])
                
                # Add statistical annotations to the plot
                for i, quartile in enumerate(quartile_stats.index):
                    stats_text = (f"Mean: {quartile_stats.loc[quartile, 'mean']:.2f}\n"
                                 f"Median: {quartile_stats.loc[quartile, 'median']:.2f}\n"
                                 f"Count: {int(quartile_stats.loc[quartile, 'count'])}")
                    ax.text(
                        i, 
                        filtered_data['Employment'].min(), 
                        stats_text, 
                        ha='center',
                        va='bottom',
                        fontsize=8,
                        bbox=dict(facecolor='white', alpha=0.7)
                    )
                
                # Show the plot
                st.pyplot(fig)
                
                # Show the data table
                with st.expander("View Data Table"):
                    # Format GDP with commas for thousands
                    display_data = filtered_data.copy()
                    display_data['GDP_per_capita'] = display_data['GDP_per_capita'].apply(lambda x: f"${x:,.2f}")
                    st.dataframe(display_data)
                
                # Add interpretation
                st.markdown("""
                **Interpreting Employment in the Transport Sector Across Economic Development Levels**
                
                This boxplot visualization shows how employment in the transport sector varies across countries 
                at different levels of economic development (GDP per capita quartiles).
                
                **Key insights to consider:**
                
                1. **Sectoral development**: In general, do more economically developed countries have higher 
                   or lower percentages of their workforce in transportation?
                
                2. **Economic transition**: As countries develop (move from lower to higher GDP quartiles), 
                   does the transport sector typically employ more or fewer people as a percentage of total employment?
                
                3. **Outliers**: Which countries have unusually high or low transport employment compared to 
                   peers in the same economic development bracket?
                
                4. **Specialization**: Some countries may specialize in transportation and logistics as a 
                   core economic activity, which would be reflected in higher employment percentages.
                
                5. **Automation impact**: More developed economies might show lower transport employment 
                   percentages due to higher automation and efficiency in the sector.
                
                The boxplot shows the median (center line), interquartile range (box), and range (whiskers) 
                of transport sector employment for each GDP quartile, allowing for direct comparison 
                of distributions across development levels.
                """)
                
                # Run a statistical test to check for significant differences between quartiles
                if len(quartile_stats) > 1 and all(quartile_stats['count'] > 1):
                    from scipy import stats
                    
                    # Perform ANOVA test
                    groups = [filtered_data[filtered_data['GDP_Quartile'] == q]['Employment'].values 
                             for q in filtered_data['GDP_Quartile'].unique()]
                    
                    # Only run the test if we have at least 2 groups with data
                    valid_groups = [g for g in groups if len(g) > 0]
                    if len(valid_groups) >= 2:
                        try:
                            f_stat, p_value = stats.f_oneway(*valid_groups)
                            
                            # Display the results
                            st.subheader("Statistical Analysis")
                            st.write(f"ANOVA F-statistic: {f_stat:.2f}")
                            st.write(f"p-value: {p_value:.4f}")
                            
                            if p_value < 0.05:
                                st.success("There is a statistically significant difference in transport employment between GDP quartiles (p < 0.05).")
                            else:
                                st.info("No statistically significant difference in transport employment between GDP quartiles (p > 0.05).")
                        except:
                            st.warning("Could not perform statistical test due to insufficient or invalid data.")
            else:
                st.warning("No countries have both GDP and transport employment data.")
        else:
            st.error(f"Required GDP column '{gdp_col}' not found in economic data.")
    else:
        st.error("No transport sector employment metrics found in the data.")


# Tab 4: Transport Investment trends vs GDP trends
with tab4:
    st.header("Economic Growth and Transportation Investment Over Time")
    
    # Find the GDP per capita time series in economic data
    gdp_per_capita_cols = [col for col in econ_annual.columns 
                           if "GDP" in col and "capita" in col and "dollars" in col.lower()]
    
    # Find investment as % of GDP in transport data
    investment_gdp_cols = [col for col in transport_annual.columns 
                           if "Investment" in col and "Percentage of GDP" in col]
    
    if gdp_per_capita_cols and investment_gdp_cols:
        # Select one GDP metric and one investment metric
        col1, col2 = st.columns(2)
        
        with col1:
            selected_gdp = st.selectbox(
                "Select GDP per Capita Metric",
                options=gdp_per_capita_cols,
                index=0 if gdp_per_capita_cols else 0
            )
        
        with col2:
            selected_inv = st.selectbox(
                "Select Investment as % of GDP Metric",
                options=investment_gdp_cols,
                index=0 if investment_gdp_cols else 0
            )
        
        # Get time series data for selected countries
        if selected_countries:
            # Filter GDP data
            gdp_data = econ_annual[econ_annual['Reference area'].isin(selected_countries)]
            gdp_data = gdp_data[['Reference area', 'TIME_PERIOD', selected_gdp]].dropna()
            
            # Filter investment data
            inv_data = transport_annual[transport_annual['Reference area'].isin(selected_countries)]
            inv_data = inv_data[['Reference area', 'TIME_PERIOD', selected_inv]].dropna()
            
            # Check if we have data
            if gdp_data.empty or inv_data.empty:
                st.warning("No time series data available for the selected countries and metrics.")
            else:
                # Create tabs for different visualization modes
                ts_tab1, ts_tab2, ts_tab3 = st.tabs(["Individual Country Comparisons", 
                                                     "GDP per Capita Trends", 
                                                     "Investment % of GDP Trends"])
                
                # Tab 1: Individual country comparisons (dual y-axis)
                with ts_tab1:
                    st.subheader("GDP per Capita vs Investment as % of GDP")
                    
                    # Allow user to select a specific country for detailed analysis
                    common_countries = list(set(gdp_data['Reference area'].unique()) & 
                                           set(inv_data['Reference area'].unique()))
                    
                    if common_countries:
                        selected_country = st.selectbox(
                            "Select a country for detailed time series analysis",
                            options=sorted(common_countries)
                        )
                        
                        # Filter data for selected country
                        country_gdp = gdp_data[gdp_data['Reference area'] == selected_country]
                        country_inv = inv_data[inv_data['Reference area'] == selected_country]
                        
                        # Merge the data on year
                        country_data = pd.merge(
                            country_gdp, 
                            country_inv, 
                            on=['Reference area', 'TIME_PERIOD'],
                            suffixes=('_gdp', '_inv')
                        )
                        
                        if not country_data.empty:
                            # Create dual y-axis plot
                            fig, ax1 = plt.subplots(figsize=(12, 6))
                            
                            # Plot GDP per capita on left y-axis
                            color = 'tab:blue'
                            ax1.set_xlabel('Year')
                            ax1.set_ylabel('GDP per Capita', color=color)
                            ax1.plot(country_data['TIME_PERIOD'], country_data[selected_gdp], 
                                    color=color, marker='o', linestyle='-', linewidth=2)
                            ax1.tick_params(axis='y', labelcolor=color)
                            
                            # Create second y-axis for investment as % of GDP
                            ax2 = ax1.twinx()
                            color = 'tab:red'
                            ax2.set_ylabel('Investment as % of GDP', color=color)
                            ax2.plot(country_data['TIME_PERIOD'], country_data[selected_inv], 
                                    color=color, marker='s', linestyle='--', linewidth=2)
                            ax2.tick_params(axis='y', labelcolor=color)
                            
                            # Add grid and title
                            ax1.grid(True, alpha=0.3)
                            plt.title(f"{selected_country}: GDP per Capita vs Transportation Investment")
                            
                            # Add legend
                            gdp_line = plt.Line2D([0], [0], color='tab:blue', linewidth=2, marker='o', linestyle='-')
                            inv_line = plt.Line2D([0], [0], color='tab:red', linewidth=2, marker='s', linestyle='--')
                            plt.legend([gdp_line, inv_line], 
                                      ['GDP per Capita', 'Investment as % of GDP'],
                                      loc='upper left')
                            
                            # Improve x-axis ticks
                            plt.xticks(country_data['TIME_PERIOD'].unique()[::2])  # Show every other year
                            
                            plt.tight_layout()
                            st.pyplot(fig)
                            
                            # Calculate and display correlation
                            correlation = country_data[selected_gdp].corr(country_data[selected_inv])
                            st.metric(
                                "Correlation between GDP per Capita and Investment",
                                f"{correlation:.2f}"
                            )
                            
                            # Add interpretation
                            if correlation > 0.5:
                                st.info("Strong positive correlation: As the economy grows, infrastructure investment grows proportionally or faster.")
                            elif correlation > 0.2:
                                st.info("Moderate positive correlation: Economic growth tends to be accompanied by increased infrastructure investment.")
                            elif correlation > -0.2:
                                st.info("Weak or no correlation: Infrastructure investment seems independent of economic growth.")
                            elif correlation > -0.5:
                                st.info("Moderate negative correlation: Infrastructure investment as a % of GDP tends to decrease as the economy grows.")
                            else:
                                st.info("Strong negative correlation: Infrastructure investment as a % of GDP significantly decreases as the economy grows.")
                        else:
                            st.warning(f"No matching time periods found for {selected_country}.")
                    else:
                        st.warning("No countries have both GDP and investment time series data.")
                
                # Tab 2: GDP per Capita trends for all selected countries
                with ts_tab2:
                    st.subheader("GDP per Capita Trends by Country")
                    
                    # Create line plot for GDP per capita
                    fig, ax = plt.subplots(figsize=(12, 6))
                    
                    # Get unique countries
                    countries = gdp_data['Reference area'].unique()
                    
                    # Plot each country
                    for country in countries:
                        country_data = gdp_data[gdp_data['Reference area'] == country]
                        ax.plot(country_data['TIME_PERIOD'], country_data[selected_gdp], 
                               marker='o', linewidth=2, label=country)
                    
                    ax.set_xlabel('Year')
                    ax.set_ylabel('GDP per Capita')
                    ax.set_title('GDP per Capita Trends')
                    ax.grid(True, alpha=0.3)
                    ax.legend()
                    
                    # Improve x-axis ticks if many years
                    years = sorted(gdp_data['TIME_PERIOD'].unique())
                    if len(years) > 10:
                        # Show fewer ticks if many years
                        ax.set_xticks(years[::2])
                    else:
                        ax.set_xticks(years)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                
                # Tab 3: Investment as % of GDP trends for all selected countries
                with ts_tab3:
                    st.subheader("Transportation Investment as % of GDP by Country")
                    
                    # Create line plot for investment
                    fig, ax = plt.subplots(figsize=(12, 6))
                    
                    # Get unique countries
                    countries = inv_data['Reference area'].unique()
                    
                    # Plot each country
                    for country in countries:
                        country_data = inv_data[inv_data['Reference area'] == country]
                        ax.plot(country_data['TIME_PERIOD'], country_data[selected_inv], 
                               marker='s', linewidth=2, label=country)
                    
                    ax.set_xlabel('Year')
                    ax.set_ylabel('Investment as % of GDP')
                    ax.set_title('Transportation Investment Trends')
                    ax.grid(True, alpha=0.3)
                    ax.legend()
                    
                    # Improve x-axis ticks if many years
                    years = sorted(inv_data['TIME_PERIOD'].unique())
                    if len(years) > 10:
                        # Show fewer ticks if many years
                        ax.set_xticks(years[::2])
                    else:
                        ax.set_xticks(years)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                
                # Add explanation
                st.markdown("""
                **Interpreting Economic Growth and Transportation Investment Time Series**
                
                These visualizations show the relationship between economic growth (GDP per capita) and transportation infrastructure investment over time.
                
                **Key insights to look for:**
                
                1. **Investment timing:** Do transportation investments precede economic growth, suggesting they may be drivers of growth?
                
                2. **Investment cycles:** Are there cycles of investment followed by periods of economic growth?
                
                3. **Economic shocks:** How do transportation investments respond to economic shocks or recessions?
                
                4. **Policy changes:** Can you identify periods where policy changes led to increases or decreases in infrastructure investment?
                
                5. **Proportional investment:** As economies grow, do they maintain, increase, or decrease the percentage of GDP dedicated to transportation infrastructure?
                
                The correlation coefficient provides a quantitative measure of the relationship between economic growth and transportation investment for each country.
                """)
        else:
            st.warning("Please select at least one country to view time series data.")
    else:
        st.error("Required GDP per capita or investment metrics not found in the data.")


with tab5:
    st.header("Rail Investment vs trend in CO2 Emissions")
    
    # Visualization 1: Rail Investment vs CO2 Emissions Trend (Slope)
    st.subheader("1. Rail Investment Impact on CO2 Emissions Trend")
    
    # Get GDP data for creating quartiles
    gdp_col = "Gross domestic product (GDP) (Total): US dollars/capita_pred2000"
    x_col = 'Investment (Rail): US dollars per person_pred2000'
    y_col = 'CO2 emissions in transport sector: Tonnes of CO2 per person_slope'  # Using slope instead of pred2000
    
    if gdp_col in econ_wide.columns and x_col in transport_wide.columns and y_col in transport_wide.columns:
        # Merge transport and economic data
        data_rows = []
        common_countries = set(transport_wide.index) & set(econ_wide.index)
        
        for country in common_countries:
            if (pd.notna(transport_wide.loc[country, x_col]) and 
                pd.notna(transport_wide.loc[country, y_col]) and 
                pd.notna(econ_wide.loc[country, gdp_col])):
                data_rows.append({
                    'Country': country,
                    'Rail_Investment': transport_wide.loc[country, x_col],
                    'CO2_Emissions_Trend': transport_wide.loc[country, y_col],
                    'GDP_per_capita': econ_wide.loc[country, gdp_col]
                })
        
        merged_data = pd.DataFrame(data_rows)
        
        if not merged_data.empty:
            # Create GDP quartiles
            merged_data['GDP_Quartile'] = pd.qcut(
                merged_data['GDP_per_capita'], 
                4, 
                labels=['Q1 (Lowest GDP)', 'Q2', 'Q3', 'Q4 (Highest GDP)']
            )
            
            # Create visualization
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Define color palette
            palette = sns.color_palette("viridis", 4)
            
            # Plot points colored by GDP quartile
            for i, quartile in enumerate(merged_data['GDP_Quartile'].cat.categories):
                quartile_data = merged_data[merged_data['GDP_Quartile'] == quartile]
                
                # Plot the scatter points
                sns.scatterplot(
                    data=quartile_data,
                    x='Rail_Investment',
                    y='CO2_Emissions_Trend',
                    label=quartile,
                    color=palette[i],
                    s=100,
                    ax=ax
                )
                
                # Add country labels
                for _, row in quartile_data.iterrows():
                    ax.annotate(
                        row['Country'],
                        (row['Rail_Investment'], row['CO2_Emissions_Trend']),
                        fontsize=8,
                        alpha=0.7,
                        xytext=(5, 5),
                        textcoords='offset points'
                    )
                
                # Add horizontal line showing average CO2 emissions trend for this quartile
                avg_co2_trend = quartile_data['CO2_Emissions_Trend'].mean()
                ax.axhline(
                    y=avg_co2_trend,
                    color=palette[i],
                    linestyle='--',
                    alpha=0.5,
                    xmin=0,
                    xmax=quartile_data['Rail_Investment'].max() / merged_data['Rail_Investment'].max()
                )
                
                # Add label for the average line
                ax.text(
                    merged_data['Rail_Investment'].max() * 0.95,
                    avg_co2_trend,
                    f"{quartile}: {avg_co2_trend:.4f}",
                    color=palette[i],
                    va='center',
                    ha='right',
                    fontsize=8,
                    bbox=dict(facecolor='white', alpha=0.7)
                )
                
                # Add trendline for each quartile if there are enough points
                if len(quartile_data) >= 3:  # Need at least 3 points for a meaningful trendline
                    sns.regplot(
                        data=quartile_data,
                        x='Rail_Investment',
                        y='CO2_Emissions_Trend',
                        scatter=False,
                        color=palette[i],
                        line_kws={'linestyle': '-', 'linewidth': 1.5, 'alpha': 0.7},
                        ax=ax
                    )
            
            # Add a horizontal line at y=0 to show the threshold between increasing/decreasing emissions
            ax.axhline(y=0, color='red', linestyle='-', alpha=0.3)
            ax.text(
                merged_data['Rail_Investment'].min(),
                0.01,
                "Increasing emissions →",
                color='darkred',
                va='bottom',
                fontsize=8
            )
            ax.text(
                merged_data['Rail_Investment'].min(),
                -0.01,
                "Decreasing emissions →",
                color='darkgreen',
                va='top',
                fontsize=8
            )
            
            # Customize the plot
            ax.set_xlabel('Investment in Rail (US Dollars per Person)', fontsize=12)
            ax.set_ylabel('CO2 Emissions Trend (Tonnes per Person per Year)', fontsize=12)
            ax.set_title('Rail Investment vs. CO2 Emissions Trend by GDP Per Capita', fontsize=14)
            
            # Calculate correlation for all data
            correlation = merged_data['Rail_Investment'].corr(merged_data['CO2_Emissions_Trend'])
            ax.text(
                0.05, 0.05,
                f'Overall Correlation: {correlation:.2f}',
                transform=ax.transAxes,
                fontsize=10,
                bbox=dict(facecolor='white', alpha=0.7)
            )
            
            # Show the legend
            ax.legend(title='GDP Per Capita Quartile', fontsize=10, title_fontsize=12)
            
            # Add grid for better readability
            ax.grid(True, alpha=0.3)
            
            # Show the plot
            st.pyplot(fig)
            
            # Add explanation
            st.markdown("""
            **Hypothesis: Countries with greater investment in rail infrastructure tend to have better (decreasing) 
            CO2 emissions trends, even when accounting for differences in economic development.**
            
            **Interpretation:**
            - Points above the red line (y=0) show countries with increasing CO2 emissions over time
            - Points below the red line show countries with decreasing CO2 emissions over time
            - Countries are grouped by GDP per capita quartiles to control for level of industrialization
            - Horizontal dashed lines show the average emissions trend for each GDP quartile
            - Countries in the bottom right (high rail investment, negative emissions trend) are performing best
            - The correlation coefficient measures the strength of the relationship between rail investment and emissions trend
            
            This visualization helps identify whether higher rail investment correlates with better emissions management
            while controlling for economic development level.
            """)
            
            # Display the data table
            with st.expander("Show Data Table"):
                st.dataframe(merged_data[['Country', 'Rail_Investment', 'CO2_Emissions_Trend', 'GDP_per_capita', 'GDP_Quartile']])
        else:
            st.warning("Insufficient data to create the visualization after merging datasets.")
    else:
        st.error("Required columns not found for Rail Investment vs CO2 Emissions Trend visualization.")
    
