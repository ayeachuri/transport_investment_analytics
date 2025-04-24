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

# Tab 3: Investment Efficiency
# Tab 3: Investment Efficiency with Rail Network and Transit Cost
with tab3:
    st.header("Rail Network Growth vs Transit Cost Efficiency")
    
    # Define the columns
    x_col = 'Transport infrastructure: Percentage of rail network_slope'
    y_col = 'National traffic: Seat-kilometres per 1 000 US dollars_slope'
    
    if x_col in transport_wide.columns and y_col in transport_wide.columns:
        # Get data for countries with both metrics
        data_rows = []
        
        for country in transport_wide.index:
            if pd.notna(transport_wide.loc[country, x_col]) and pd.notna(transport_wide.loc[country, y_col]):
                # Check if GDP data is available for this country
                gdp_value = econ_wide.loc[country, gdp_col] if country in econ_wide.index and pd.notna(econ_wide.loc[country, gdp_col]) else np.nan
                
                data_rows.append({
                    'Country': country,
                    'Rail_Network_Trend': transport_wide.loc[country, x_col],
                    'Transit_Efficiency_Trend': transport_wide.loc[country, y_col],
                    'GDP_per_capita': gdp_value
                })
        
        efficiency_data = pd.DataFrame(data_rows)
        
        if not efficiency_data.empty:
            # Convert the raw trend values to percentile ranks for the y-axis
            # This addresses the scale issues by making it an ordinal list
            efficiency_data['Transit_Efficiency_Percentile'] = efficiency_data['Transit_Efficiency_Trend'].rank(pct=True) * 100
            
            # Create GDP quartiles where GDP data is available
            valid_gdp = efficiency_data['GDP_per_capita'].notna()
            if valid_gdp.sum() >= 4:  # Need at least 4 points for quartiles
                efficiency_data.loc[valid_gdp, 'GDP_Quartile'] = pd.qcut(
                    efficiency_data.loc[valid_gdp, 'GDP_per_capita'], 
                    4, 
                    labels=['Q1 (Lowest GDP)', 'Q2', 'Q3', 'Q4 (Highest GDP)']
                )
            else:
                efficiency_data['GDP_Quartile'] = 'Unknown'
            
            # Filter for selected countries
            if selected_countries:
                plot_data = efficiency_data[efficiency_data['Country'].isin(selected_countries)]
                
                if plot_data.empty:
                    st.warning("None of the selected countries have data for both rail network and transit efficiency trends.")
                    return
            else:
                plot_data = efficiency_data
            
            # Create visualization
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Define color palette
            palette = sns.color_palette("viridis", 4)
            
            # Plot points colored by GDP quartile if available
            if 'Unknown' not in plot_data['GDP_Quartile'].unique():
                # Convert categorical to string before ordering
                quartiles = plot_data['GDP_Quartile'].astype(str).unique()
                # Use a fixed order for quartiles
                quartile_order = ['Q1 (Lowest GDP)', 'Q2', 'Q3', 'Q4 (Highest GDP)']
                # Only use quartiles that exist in the data
                ordered_quartiles = [q for q in quartile_order if q in quartiles]
                
                for i, quartile in enumerate(ordered_quartiles):
                    quartile_data = plot_data[plot_data['GDP_Quartile'] == quartile]
                    
                    # Plot the scatter points
                    sns.scatterplot(
                        data=quartile_data,
                        x='Rail_Network_Trend',
                        y='Transit_Efficiency_Percentile',  # Using percentile instead of raw value
                        label=quartile,
                        color=palette[i],
                        s=100,
                        ax=ax
                    )
                    
                    # Add country labels
                    for _, row in quartile_data.iterrows():
                        ax.annotate(
                            row['Country'],
                            (row['Rail_Network_Trend'], row['Transit_Efficiency_Percentile']),
                            fontsize=8,
                            alpha=0.7,
                            xytext=(5, 5),
                            textcoords='offset points'
                        )
                    
                    # Add trendline for each quartile if there are enough points
                    if len(quartile_data) >= 3:
                        sns.regplot(
                            data=quartile_data,
                            x='Rail_Network_Trend',
                            y='Transit_Efficiency_Percentile',  # Using percentile instead of raw value
                            scatter=False,
                            color=palette[i],
                            line_kws={'linestyle': '-', 'linewidth': 1.5, 'alpha': 0.7},
                            ax=ax
                        )
            else:
                # Plot all points in one color if no GDP quartiles
                sns.scatterplot(
                    data=plot_data,
                    x='Rail_Network_Trend',
                    y='Transit_Efficiency_Percentile',  # Using percentile instead of raw value
                    s=100,
                    ax=ax
                )
                
                # Add country labels
                for _, row in plot_data.iterrows():
                    ax.annotate(
                        row['Country'],
                        (row['Rail_Network_Trend'], row['Transit_Efficiency_Percentile']),
                        fontsize=8,
                        alpha=0.7,
                        xytext=(5, 5),
                        textcoords='offset points'
                    )
            
            # Add quadrant lines and labels (at median/50% for y-axis percentile)
            ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
            ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
            
            # Add quadrant labels
            ax.text(
                plot_data['Rail_Network_Trend'].max() * 0.7,
                75,
                "Growing rail network\nTop efficiency trends",
                ha='center',
                bbox=dict(facecolor='green', alpha=0.1)
            )
            
            ax.text(
                plot_data['Rail_Network_Trend'].min() * 0.7,
                25,
                "Shrinking rail network\nBottom efficiency trends",
                ha='center',
                bbox=dict(facecolor='red', alpha=0.1)
            )
            
            # Customize the plot
            ax.set_xlabel('Trend in Rail Network Percentage (Annual Change)', fontsize=12)
            ax.set_ylabel('Transit Cost Efficiency Trend (Percentile Rank)', fontsize=12)
            ax.set_title('Relationship Between Rail Network Growth and Transit Cost Efficiency', fontsize=14)
            ax.set_ylim(0, 100)  # Set y-axis from 0 to 100 for percentiles
            
            # Add percentile labels on y-axis
            ax.set_yticks([0, 25, 50, 75, 100])
            ax.set_yticklabels(['0% (Worst)', '25%', '50% (Median)', '75%', '100% (Best)'])
            
            # Calculate correlation between rail network trend and efficiency percentile
            correlation = plot_data['Rail_Network_Trend'].corr(plot_data['Transit_Efficiency_Percentile'])
            ax.text(
                0.05, 0.95,
                f'Correlation: {correlation:.2f}',
                transform=ax.transAxes,
                fontsize=10,
                bbox=dict(facecolor='white', alpha=0.7)
            )
            
            # Show the legend if GDP quartiles are available
            if 'Unknown' not in plot_data['GDP_Quartile'].unique():
                ax.legend(title='GDP Per Capita Quartile', fontsize=10, title_fontsize=12)
            
            # Add grid for better readability
            ax.grid(True, alpha=0.3)
            
            # Show the plot
            st.pyplot(fig)
            
            # Add explanation
            st.markdown("""
            **Hypothesis: Countries that are expanding their rail networks tend to see improvements in public 
            transit cost efficiency.**
            
            **Interpretation:**
            - The y-axis shows percentile ranks of efficiency trends (from worst to best)
            - Points in the upper right quadrant show countries with both growing rail networks and improving transit efficiency
            - Points in the lower left quadrant show countries with shrinking rail networks and declining efficiency
            - The correlation coefficient measures the strength of the relationship between rail network growth and efficiency trends
            - Positive correlation supports the hypothesis that expanding rail networks improves transit cost efficiency
            
            This visualization helps identify whether countries that invest in expanding their rail networks 
            achieve better cost efficiency in their national transit systems. Using percentile rankings on the 
            y-axis allows for easier comparisons across countries by normalizing the scale.
            """)
            
            # Display the data table
            with st.expander("Show Data Table"):
                display_data = plot_data[['Country', 'Rail_Network_Trend', 'Transit_Efficiency_Trend', 'Transit_Efficiency_Percentile', 'GDP_per_capita']]
                display_data.columns = ['Country', 'Rail Network Trend', 'Raw Efficiency Trend', 'Efficiency Percentile', 'GDP per Capita']
                st.dataframe(display_data)
        else:
            st.warning("Insufficient data to create the Rail Network vs Transit Efficiency visualization.")
    else:
        st.error("Required columns not found for Rail Network vs Transit Efficiency visualization.")

# Tab 4: Economic Impact
with tab4:
    st.header("Economic Impact of Transportation Investment")
    
    # Get available economic indicators
    econ_indicators = [col for col in econ_wide.columns if 'pred2000' in col]
    transport_investment = [col for col in transport_wide.columns if 'Investment' in col and 'pred2000' in col]
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_econ = st.selectbox(
            "Select Economic Indicator",
            options=econ_indicators,
            index=0 if econ_indicators else 0
        )
    
    with col2:
        selected_transport = st.selectbox(
            "Select Transportation Investment Metric",
            options=transport_investment,
            index=0 if transport_investment else 0
        )
    
    if selected_econ and selected_transport and selected_countries:
        # Create a merged dataframe with both transport and economic data
        data_rows = []
        
        for country in selected_countries:
            if country in transport_wide.index and country in econ_wide.index:
                transport_value = transport_wide.loc[country, selected_transport]
                econ_value = econ_wide.loc[country, selected_econ]
                
                data_rows.append({
                    'Country': country,
                    'Transport': transport_value,
                    'Economic': econ_value
                })
        
        merged_data = pd.DataFrame(data_rows)
        
        if not merged_data.empty:
            # Create the scatter plot
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot the data
            sns.scatterplot(
                data=merged_data,
                x='Transport',
                y='Economic',
                s=100,
                ax=ax
            )
            
            # Add country labels
            for i, row in merged_data.iterrows():
                ax.annotate(
                    row['Country'],
                    (row['Transport'], row['Economic']),
                    xytext=(5, 5),
                    textcoords='offset points'
                )
            
            # Add regression line
            sns.regplot(
                data=merged_data,
                x='Transport',
                y='Economic',
                scatter=False,
                ax=ax,
                color='red',
                line_kws={'linestyle': '--'}
            )
            
            # Clean labels
            transport_label = selected_transport.split('_pred2000')[0]
            econ_label = selected_econ.split('_pred2000')[0]
            
            ax.set_xlabel(transport_label)
            ax.set_ylabel(econ_label)
            ax.set_title(f'Relationship between {transport_label} and {econ_label}')
            
            # Calculate correlation
            correlation = merged_data['Transport'].corr(merged_data['Economic'])
            ax.text(
                0.05, 0.95,
                f'Correlation: {correlation:.2f}',
                transform=ax.transAxes,
                bbox=dict(facecolor='white', alpha=0.7)
            )
            
            st.pyplot(fig)
            
            # Add explanation
            st.markdown(f"""
            **Economic Impact Analysis:**
            
            This chart explores the relationship between **{transport_label}** and **{econ_label}** for the selected countries.
            
            - The correlation coefficient is **{correlation:.2f}** (ranges from -1 to 1)
            - A positive correlation suggests that higher transportation investment may be associated with better economic outcomes
            - A negative correlation might indicate diminishing returns or other economic factors at play
            
            *Note: Correlation does not imply causation. Other factors may influence both variables.*
            """)
            
            # Show the raw data
            st.subheader("Data for Economic Impact Analysis")
            display_data = merged_data.copy()
            display_data.columns = ['Country', transport_label, econ_label]
            st.dataframe(display_data)
        else:
            st.warning("No matching data found for selected countries in both transport and economic datasets.")
    else:
        st.warning("Please select both economic and transportation metrics for the impact analysis.")


with tab5:
    st.header("Advanced Analysis: Investment Impact on Emissions and Efficiency")
    
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
    
