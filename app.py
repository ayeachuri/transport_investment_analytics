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
    "Road Network Reliance vs CO2 emissions per person", 
    "Road Investment and Traffic Safety", 
    "Employment in Transport Sector",
    "GDP Growth vs Transport Investment as \% \of GDP",
    "Rail investment vs CO2"
])

# Tab 1: Road Network vs CO2 Emissions
with tab1:
    st.header("Road Network Focus vs CO2 Emissions")
    
    # Find the road network percentage column
    road_network_cols = [col for col in transport_wide.columns 
                        if "Transport infrastructure: Percentage of road network" in col and "pred2000" in col]
    
    # Find CO2 emissions per person column
    co2_person_cols = [col for col in transport_wide.columns 
                      if "CO2 emissions in transport sector: Tonnes of CO2 per person" in col and "pred2000" in col]
    
    if road_network_cols and co2_person_cols:
        # Get the columns (should be just one of each)
        road_col = road_network_cols[0]
        co2_col = co2_person_cols[0]
        
        # Create the scatter plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot all countries as background
        sns.scatterplot(
            x=transport_wide[road_col],
            y=transport_wide[co2_col],
            alpha=0.3,
            color='gray',
            ax=ax
        )
        
        # Highlight selected countries
        if selected_countries:
            selected_data = transport_wide.loc[selected_countries].copy()
            selected_data = selected_data.dropna(subset=[road_col, co2_col])
            
            # Only proceed if we have valid data
            if not selected_data.empty:
                # Get GDP data for selected countries if available
                gdp_col = "Gross domestic product (GDP) (Total): US dollars/capita_pred2000"
                
                if gdp_col in econ_wide.columns:
                    for country in selected_data.index:
                        if country in econ_wide.index and pd.notna(econ_wide.loc[country, gdp_col]):
                            selected_data.loc[country, 'GDP_per_capita'] = econ_wide.loc[country, gdp_col]
                        else:
                            selected_data.loc[country, 'GDP_per_capita'] = np.nan
                    
                    # Create GDP quartiles where GDP data is available
                    valid_gdp = selected_data['GDP_per_capita'].notna()
                    if valid_gdp.sum() >= 4:  # Need at least 4 points for quartiles
                        selected_data.loc[valid_gdp, 'GDP_Quartile'] = pd.qcut(
                            selected_data.loc[valid_gdp, 'GDP_per_capita'], 
                            4, 
                            labels=['Q1 (Lowest GDP)', 'Q2', 'Q3', 'Q4 (Highest GDP)']
                        )
                    else:
                        selected_data['GDP_Quartile'] = 'Unknown'
                    
                    # Plot with color by GDP quartile if available
                    if 'GDP_Quartile' in selected_data.columns and 'Unknown' not in selected_data['GDP_Quartile'].unique():
                        # Convert categorical to string before ordering
                        quartiles = selected_data['GDP_Quartile'].astype(str).unique()
                        # Use a fixed order for quartiles
                        quartile_order = ['Q1 (Lowest GDP)', 'Q2', 'Q3', 'Q4 (Highest GDP)']
                        # Only use quartiles that exist in the data
                        ordered_quartiles = [q for q in quartile_order if q in quartiles]
                        
                        sns.scatterplot(
                            data=selected_data,
                            x=road_col,
                            y=co2_col,
                            hue='GDP_Quartile',
                            hue_order=ordered_quartiles,
                            palette='viridis',
                            s=100,
                            ax=ax
                        )
                    else:
                        # Fallback if no GDP data
                        sns.scatterplot(
                            data=selected_data,
                            x=road_col,
                            y=co2_col,
                            hue=selected_data.index,
                            s=100,
                            ax=ax
                        )
                else:
                    # Fallback if no GDP data
                    sns.scatterplot(
                        data=selected_data,
                        x=road_col,
                        y=co2_col,
                        hue=selected_data.index,
                        s=100,
                        ax=ax
                    )
                
                # Add annotations for selected countries
                for country in selected_data.index:
                    x = selected_data.loc[country, road_col]
                    y = selected_data.loc[country, co2_col]
                    ax.annotate(country, (x, y), xytext=(5, 5), textcoords='offset points')
        
        # Add regression line
        sns.regplot(
            x=transport_wide[road_col],
            y=transport_wide[co2_col],
            scatter=False,
            ax=ax,
            color='red',
            line_kws={'linestyle': '--'}
        )
        
        # Calculate correlation
        valid_data = transport_wide.dropna(subset=[road_col, co2_col])
        correlation = valid_data[road_col].corr(valid_data[co2_col])
        
        # Add correlation text
        ax.text(
            0.05, 0.95,
            f'Correlation: {correlation:.2f}',
            transform=ax.transAxes,
            fontsize=10,
            bbox=dict(facecolor='white', alpha=0.7)
        )
        
        # Clean up the column names for the axis labels
        x_label = road_col.split('_pred2000')[0]
        y_label = co2_col.split('_pred2000')[0]
        
        ax.set_xlabel(x_label, fontsize=11)
        ax.set_ylabel(y_label, fontsize=11)
        ax.set_title(f'Relationship between Road Network Focus and CO2 Emissions', fontsize=14)
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3)
        
        # Show the plot
        st.pyplot(fig)
        
        # Add explanation
        st.markdown(f"""
        **Road Infrastructure Focus vs CO2 Emissions**
        
        This scatter plot examines the relationship between a country's focus on road infrastructure 
        (measured as percentage of transport infrastructure that is road network) and carbon emissions 
        per person from the transport sector.
        
        **Key findings:**
        
        - The correlation coefficient between road network percentage and CO2 emissions is **{correlation:.2f}**
        - {'A positive correlation suggests that countries with greater road focus tend to have higher emissions.' if correlation > 0 else 'This analysis does not show a strong relationship between road focus and emissions.'}
        - {'Countries with a stronger emphasis on alternative transportation modes (rail, water, etc.) appear to have lower per capita emissions.' if correlation > 0.3 else ''}
        
        **Interpretation:**
        Road-dominant transportation systems typically rely heavily on private vehicles, which are less 
        energy-efficient per passenger than mass transit options like rail. This relationship highlights 
        the environmental impact of transportation infrastructure choices.
        
        Different development patterns (urban density, city planning, geographic constraints) may explain 
        why some countries deviate significantly from the trend line.
        """)
        
        # Show the data in a table
        if selected_countries:
            with st.expander("Show Data for Selected Countries"):
                display_data = transport_wide.loc[selected_countries, [road_col, co2_col]].copy().dropna()
                display_data.columns = [x_label, y_label]
                st.dataframe(display_data)
    else:
        st.error("Required road network or CO2 emissions metrics not found in the data.")

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
# Tab 4: GDP Growth by Transport Investment Quartiles
with tab4:
    st.header("GDP Growth Rates by Transport Investment Level")
    
    # Find GDP columns in economic data
    gdp_cols = [col for col in econ_annual.columns 
               if "GDP" in col and "Total" in col and "US dollars" in col]
    
    # Find investment as % of GDP columns in transport data
    investment_gdp_cols = [col for col in transport_wide.columns 
                          if "Investment" in col and "Percentage of GDP" in col and "pred2000" in col]
    
    if gdp_cols and investment_gdp_cols:
        # Let user select which GDP metric to use for growth calculation
        selected_gdp = st.selectbox(
            "Select GDP Metric for Growth Calculation",
            options=gdp_cols,
            index=0 if gdp_cols else 0
        )
        
        # Let user select which investment metric to use for clustering
        selected_inv = st.selectbox(
            "Select Transport Investment Metric for Clustering",
            options=investment_gdp_cols,
            index=0 if investment_gdp_cols else 0
        )
        
        # Create a dataframe with countries and their investment levels
        investment_data = []
        
        for country in transport_wide.index:
            if pd.notna(transport_wide.loc[country, selected_inv]):
                investment_data.append({
                    'Country': country,
                    'Investment': transport_wide.loc[country, selected_inv]
                })
        
        investment_df = pd.DataFrame(investment_data)
        
        if not investment_df.empty:
            # Create investment quartiles
            investment_df['Investment_Quartile'] = pd.qcut(
                investment_df['Investment'], 
                4, 
                labels=['Q1 (Lowest Investment)', 'Q2', 'Q3', 'Q4 (Highest Investment)']
            )
            
            # Calculate GDP year-on-year growth rates for each country
            gdp_growth_data = []
            
            # Process each country
            for country in econ_annual['Reference area'].unique():
                # Skip if country is not in our investment data
                if country not in investment_df['Country'].values:
                    continue
                
                # Get investment quartile for this country
                inv_quartile = investment_df.loc[investment_df['Country'] == country, 'Investment_Quartile'].values[0]
                
                # Get GDP data for this country
                country_gdp = econ_annual[
                    (econ_annual['Reference area'] == country) & 
                    pd.notna(econ_annual[selected_gdp])
                ][['TIME_PERIOD', selected_gdp]].sort_values('TIME_PERIOD')
                
                # Skip if not enough data points
                if len(country_gdp) < 2:
                    continue
                
                # Calculate year-on-year growth rates
                country_gdp['GDP_Growth'] = country_gdp[selected_gdp].pct_change() * 100  # Convert to percentage
                
                # Skip the first row which will have NaN growth rate
                country_gdp = country_gdp.dropna(subset=['GDP_Growth'])
                
                # Add country and investment quartile information
                country_gdp['Country'] = country
                country_gdp['Investment_Quartile'] = inv_quartile
                country_gdp['Investment_Value'] = investment_df.loc[investment_df['Country'] == country, 'Investment'].values[0]
                
                # Append to our growth data
                gdp_growth_data.append(country_gdp)
            
            if gdp_growth_data:
                # Combine all country data
                growth_df = pd.concat(gdp_growth_data, ignore_index=True)
                
                # Filter to selected countries if any selected
                if selected_countries:
                    filtered_growth = growth_df[growth_df['Country'].isin(selected_countries)]
                    if filtered_growth.empty:
                        st.warning("None of the selected countries have sufficient GDP data for growth calculation.")
                        # Fallback to all countries
                        filtered_growth = growth_df
                else:
                    filtered_growth = growth_df
                
                # Create tabs for different views
                growth_tab1, growth_tab2, growth_tab3 = st.tabs([
                    "Average Growth by Investment Quartile", 
                    "Growth Trends by Investment Quartile",
                    "Individual Country Growth Trends"
                ])
                
                # Tab 1: Average Growth by Investment Quartile
                with growth_tab1:
                    st.subheader("Average GDP Growth by Transport Investment Level")
                    
                    # Calculate average growth by investment quartile
                    avg_growth = filtered_growth.groupby('Investment_Quartile')['GDP_Growth'].agg(['mean', 'median', 'std', 'count']).reset_index()
                    
                    # Sort by investment quartile (they should already be in order)
                    avg_growth['quartile_order'] = avg_growth['Investment_Quartile'].apply(
                        lambda x: ['Q1 (Lowest Investment)', 'Q2', 'Q3', 'Q4 (Highest Investment)'].index(x)
                    )
                    avg_growth = avg_growth.sort_values('quartile_order').drop('quartile_order', axis=1)
                    
                    # Create bar chart
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Plot mean growth as bars
                    bars = ax.bar(
                        avg_growth['Investment_Quartile'], 
                        avg_growth['mean'],
                        yerr=avg_growth['std'],
                        capsize=5,
                        color=sns.color_palette("viridis", 4)
                    )
                    
                    # Add data labels on top of bars
                    for bar in bars:
                        height = bar.get_height()
                        ax.annotate(
                            f'{height:.2f}%',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=10
                        )
                    
                    # Add a horizontal line at y=0
                    ax.axhline(y=0, color='red', linestyle='-', alpha=0.3)
                    
                    # Customize the plot
                    ax.set_xlabel('Transport Investment Quartile', fontsize=12)
                    ax.set_ylabel('Average Annual GDP Growth (%)', fontsize=12)
                    ax.set_title('Average GDP Growth Rate by Transport Investment Level', fontsize=14)
                    ax.grid(True, axis='y', alpha=0.3)
                    
                    # Show the plot
                    st.pyplot(fig)
                    
                    # Add a data table with statistics
                    st.subheader("Summary Statistics")
                    
                    # Format the table
                    display_stats = avg_growth.copy()
                    display_stats.columns = ['Investment Quartile', 'Mean Growth (%)', 'Median Growth (%)', 'Std Dev', 'Count']
                    display_stats['Mean Growth (%)'] = display_stats['Mean Growth (%)'].round(2)
                    display_stats['Median Growth (%)'] = display_stats['Median Growth (%)'].round(2)
                    display_stats['Std Dev'] = display_stats['Std Dev'].round(2)
                    
                    st.dataframe(display_stats)
                    
                    # Run ANOVA to test if differences are significant
                    from scipy import stats
                    
                    # Create groups for ANOVA
                    groups = []
                    for quartile in avg_growth['Investment_Quartile']:
                        group_data = filtered_growth[filtered_growth['Investment_Quartile'] == quartile]['GDP_Growth'].values
                        if len(group_data) > 0:
                            groups.append(group_data)
                    
                    # Only run ANOVA if we have at least 2 groups
                    if len(groups) >= 2:
                        try:
                            f_stat, p_value = stats.f_oneway(*groups)
                            
                            # Display results
                            st.metric("ANOVA p-value", f"{p_value:.4f}")
                            
                            if p_value < 0.05:
                                st.success("There is a statistically significant difference in GDP growth rates between investment quartiles (p < 0.05).")
                            else:
                                st.info("No statistically significant difference in GDP growth rates between investment quartiles (p > 0.05).")
                        except:
                            st.warning("Could not perform statistical test due to insufficient or invalid data.")
                
                # Tab 2: Growth Trends by Investment Quartile
                with growth_tab2:
                    st.subheader("GDP Growth Trends by Transport Investment Level")
                    
                    # Calculate average growth by year and investment quartile
                    yearly_growth = filtered_growth.groupby(['TIME_PERIOD', 'Investment_Quartile'])['GDP_Growth'].mean().reset_index()
                    
                    # Create line plot
                    fig, ax = plt.subplots(figsize=(12, 6))
                    
                    # Plot each investment quartile
                    for i, quartile in enumerate(sorted(yearly_growth['Investment_Quartile'].unique())):
                        quartile_data = yearly_growth[yearly_growth['Investment_Quartile'] == quartile]
                        
                        ax.plot(
                            quartile_data['TIME_PERIOD'], 
                            quartile_data['GDP_Growth'],
                            marker='o',
                            linewidth=2,
                            label=quartile,
                            color=sns.color_palette("viridis", 4)[i]
                        )
                    
                    # Add a horizontal line at y=0
                    ax.axhline(y=0, color='red', linestyle='-', alpha=0.3)
                    
                    # Customize the plot
                    ax.set_xlabel('Year', fontsize=12)
                    ax.set_ylabel('Average GDP Growth Rate (%)', fontsize=12)
                    ax.set_title('GDP Growth Trends by Transport Investment Level', fontsize=14)
                    ax.grid(True, alpha=0.3)
                    ax.legend(title='Investment Quartile')
                    
                    # Improve x-axis ticks if many years
                    years = sorted(yearly_growth['TIME_PERIOD'].unique())
                    if len(years) > 15:
                        # Show fewer ticks if many years
                        ax.set_xticks(years[::3])
                    elif len(years) > 10:
                        ax.set_xticks(years[::2])
                    else:
                        ax.set_xticks(years)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Add explanation
                    st.markdown("""
                    **Interpreting Growth Trends by Investment Level**
                    
                    This chart shows how average GDP growth rates have evolved over time for countries in different 
                    transport investment quartiles.
                    
                    **Key patterns to look for:**
                    
                    1. **Consistent outperformance**: Do countries in higher investment quartiles consistently show 
                       higher growth rates across different time periods?
                    
                    2. **Resilience to shocks**: During economic downturns, do countries with higher transport 
                       investment show more resilience (smaller declines in growth)?
                    
                    3. **Recovery patterns**: Following economic shocks, do countries with higher transport investment 
                       recover more quickly?
                    
                    4. **Long-term trends**: Over longer periods, is there a clear relationship between investment 
                       level and average growth rates?
                    """)
                
                # Tab 3: Individual Country Growth Trends
                with growth_tab3:
                    st.subheader("Individual Country GDP Growth Trends")
                    
                    # Allow selection of specific countries for comparison
                    compare_countries = st.multiselect(
                        "Select countries to compare",
                        options=sorted(filtered_growth['Country'].unique()),
                        default=sorted(filtered_growth['Country'].unique())[:min(5, len(filtered_growth['Country'].unique()))]
                    )
                    
                    if compare_countries:
                        # Filter to selected countries
                        country_growth = filtered_growth[filtered_growth['Country'].isin(compare_countries)]
                        
                        # Create visualization
                        fig, ax = plt.subplots(figsize=(12, 6))
                        
                        # Plot each country
                        for country in compare_countries:
                            country_data = country_growth[country_growth['Country'] == country]
                            
                            if not country_data.empty:
                                # Get investment quartile for color coding
                                inv_quartile = country_data['Investment_Quartile'].iloc[0]
                                quartile_idx = ['Q1 (Lowest Investment)', 'Q2', 'Q3', 'Q4 (Highest Investment)'].index(inv_quartile)
                                
                                # Plot the country's growth trend
                                ax.plot(
                                    country_data['TIME_PERIOD'],
                                    country_data['GDP_Growth'],
                                    marker='o',
                                    linewidth=2,
                                    label=f"{country} ({inv_quartile})",
                                    color=sns.color_palette("viridis", 4)[quartile_idx]
                                )
                        
                        # Add a horizontal line at y=0
                        ax.axhline(y=0, color='red', linestyle='-', alpha=0.3)
                        
                        # Customize the plot
                        ax.set_xlabel('Year', fontsize=12)
                        ax.set_ylabel('GDP Growth Rate (%)', fontsize=12)
                        ax.set_title('Individual Country GDP Growth Trends', fontsize=14)
                        ax.grid(True, alpha=0.3)
                        ax.legend(title='Country (Investment Quartile)')
                        
                        # Improve x-axis ticks if many years
                        years = sorted(country_growth['TIME_PERIOD'].unique())
                        if len(years) > 15:
                            # Show fewer ticks if many years
                            ax.set_xticks(years[::3])
                        elif len(years) > 10:
                            ax.set_xticks(years[::2])
                        else:
                            ax.set_xticks(years)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        
                        # Show data table with investment values
                        st.subheader("Transport Investment Levels")
                        
                        inv_levels = pd.DataFrame({
                            'Country': compare_countries,
                            'Investment (% of GDP)': [
                                filtered_growth[filtered_growth['Country'] == c]['Investment_Value'].iloc[0]
                                if not filtered_growth[filtered_growth['Country'] == c].empty else np.nan
                                for c in compare_countries
                            ],
                            'Investment Quartile': [
                                filtered_growth[filtered_growth['Country'] == c]['Investment_Quartile'].iloc[0]
                                if not filtered_growth[filtered_growth['Country'] == c].empty else 'Unknown'
                                for c in compare_countries
                            ]
                        })
                        
                        # Calculate average growth rate for each country
                        avg_growth_rates = []
                        for country in compare_countries:
                            country_data = country_growth[country_growth['Country'] == country]
                            if not country_data.empty:
                                avg_growth_rates.append(country_data['GDP_Growth'].mean())
                            else:
                                avg_growth_rates.append(np.nan)
                        
                        inv_levels['Average Growth Rate (%)'] = [round(rate, 2) for rate in avg_growth_rates]
                        
                        # Sort by investment level
                        inv_levels = inv_levels.sort_values('Investment (% of GDP)', ascending=False)
                        
                        st.dataframe(inv_levels)
                    else:
                        st.warning("Please select at least one country to compare.")
                
                # Add overall interpretation
                st.markdown("""
                **Relationship Between Transport Investment and Economic Growth**
                
                This analysis explores whether countries with higher levels of transport infrastructure investment 
                (as a percentage of GDP) tend to experience higher economic growth rates.
                
                **Key considerations:**
                
                1. **Causality vs. correlation**: A positive relationship between investment and growth doesn't necessarily 
                   mean that investment causes growth. Countries with stronger economies may simply have more resources 
                   to invest in infrastructure.
                
                2. **Time lags**: Infrastructure investments may take years or even decades to fully impact economic growth. 
                   The growth benefits may not be immediately visible in the data.
                
                3. **Efficiency of investment**: The quality and efficiency of infrastructure investment matters, not just 
                   the quantity. Some countries may achieve better growth outcomes with lower but more targeted investments.
                
                4. **Context matters**: The optimal level of transport investment likely varies based on a country's existing 
                   infrastructure, geography, population density, and economic structure.
                """)
            else:
                st.warning("Insufficient GDP data to calculate growth rates for countries with investment data.")
        else:
            st.warning("No transport investment data available.")
    else:
        st.error("Required GDP or investment metrics not found in the data.")


with tab5:
    st.header("Rail Investment vs CO2 Scatterplot, clustered")
    
    # Visualization 1: Rail Investment vs CO2 Emissions Trend (Slope)
    
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
    
