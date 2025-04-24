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

# Tab 2: Investment Trends
with tab2:
    st.header("Investment Trends Over Time")

# Get investment columns from annual data
investment_trend_columns = [col for col in transport_annual.columns if 'Investment' in col]

if investment_trend_columns:
    # Select metric for time series
    selected_trend_metric = st.selectbox(
        "Select Investment Metric for Trend Analysis",
        options=investment_trend_columns,
        index=0 if investment_trend_columns else 0
    )
    
    # Filter annual data for selected countries
    if selected_countries:
        # Filter the data
        filtered_annual = transport_annual[transport_annual['Reference area'].isin(selected_countries)]
        
        # Create the time series plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Pivot data for plotting
        pivot_data = filtered_annual.pivot(index='TIME_PERIOD', columns='Reference area', values=selected_trend_metric)
        
        # Plot the data
        pivot_data.plot(marker='o', ax=ax)
        
        ax.set_title(f'{selected_trend_metric} Over Time')
        ax.set_xlabel('Year')
        ax.set_ylabel(selected_trend_metric)
        ax.grid(True, alpha=0.3)
        
        # Improve x-axis ticks
        years = sorted(filtered_annual['TIME_PERIOD'].unique())
        if len(years) > 10:
            # Show fewer x ticks if there are many years
            step = max(1, len(years) // 10)
            ax.set_xticks(years[::step])
        else:
            ax.set_xticks(years)
            
        ax.legend(title='Country')
        plt.tight_layout()
        
        st.pyplot(fig)
        
        # Add explanation
        st.markdown("""
        **Interpretation:**
        - This chart shows how investment in transportation has changed over time for the selected countries.
        - Rising trends indicate increasing investment in transportation infrastructure.
        - Declining trends may indicate shifting priorities or economic challenges.
        - Sharp changes might correspond to major policy shifts or economic events.
        """)
    else:
        st.warning("Please select at least one country to view investment trends.")
else:
    st.warning("No investment metrics found in the annual data.")

# Tab 3: Investment Efficiency
with tab3:
    st.header("Transportation Investment Efficiency Analysis")

# Create efficiency analysis for countries
if selected_countries:
    # Get investment and outcome metrics
    investment_metrics = [col for col in transport_wide.columns if 'Investment' in col and 'pred2000' in col]
    outcome_metrics = [col for col in transport_wide.columns if any(term in col for term in ['CO2', 'emissions', 'Traffic']) and 'pred2000' in col]
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_inv_metric = st.selectbox(
            "Select Investment Metric for Efficiency Analysis",
            options=investment_metrics,
            index=0 if investment_metrics else 0
        )
    
    with col2:
        selected_outcome = st.selectbox(
            "Select Outcome Metric",
            options=outcome_metrics,
            index=0 if outcome_metrics else 0
        )
    
    if selected_inv_metric and selected_outcome:
        # Create a normalized comparison (efficiency calculation)
        comparison_data = transport_wide.loc[selected_countries, [selected_inv_metric, selected_outcome]].copy()
        
        # For emissions/negative outcomes, lower is better
        if any(term in selected_outcome for term in ['CO2', 'emissions', 'pollution']):
            # Invert the outcome so lower emissions = higher efficiency
            comparison_data['efficiency'] = 1 / (comparison_data[selected_outcome] / comparison_data[selected_inv_metric])
        else:
            # For positive outcomes, higher is better
            comparison_data['efficiency'] = comparison_data[selected_outcome] / comparison_data[selected_inv_metric]
        
        # Sort by efficiency
        comparison_data = comparison_data.sort_values('efficiency', ascending=False)
        
        # Create a bar chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot the bars
        bars = ax.bar(comparison_data.index, comparison_data['efficiency'], color='skyblue')
        
        # Add labels
        ax.set_title('Investment Efficiency Analysis')
        ax.set_xlabel('Country')
        ax.set_ylabel('Efficiency Score (Outcome per Investment Unit)')
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}',
                    ha='center', va='bottom', rotation=0)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Add explanation
        st.markdown(f"""
        **Investment Efficiency Analysis:**
        
        This chart shows how efficiently countries convert their transportation investments into desirable outcomes.
        
        - For **{selected_inv_metric.split('_pred2000')[0]}** vs **{selected_outcome.split('_pred2000')[0]}**
        - Higher bars indicate greater efficiency (more outcome per unit of investment)
        - Countries at the left achieve better results with their investment
        
        *Note: For emissions or negative outcomes, the efficiency is calculated as inversely proportional to the outcome.*
        """)
        
        # Show the raw data
        st.subheader("Raw Data for Efficiency Analysis")
        display_data = comparison_data.copy()
        display_data.columns = [
            selected_inv_metric.split('_pred2000')[0], 
            selected_outcome.split('_pred2000')[0], 
            'Efficiency Score'
        ]
        st.dataframe(display_data)
        
    else:
        st.warning("Please select both investment and outcome metrics for the efficiency analysis.")

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
    
    # Visualization 2: Rail Network Trend vs Traffic Efficiency Trend
    st.subheader("2. Rail Network Growth vs Transit Cost Efficiency")
    
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
            
            # Create visualization
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Define color palette
            palette = sns.color_palette("viridis", 4)
            
            # Plot points colored by GDP quartile if available
            if 'Unknown' not in efficiency_data['GDP_Quartile'].unique():
                for i, quartile in enumerate(sorted(efficiency_data['GDP_Quartile'].unique())):
                    quartile_data = efficiency_data[efficiency_data['GDP_Quartile'] == quartile]
                    
                    # Plot the scatter points
                    sns.scatterplot(
                        data=quartile_data,
                        x='Rail_Network_Trend',
                        y='Transit_Efficiency_Trend',
                        label=quartile,
                        color=palette[i],
                        s=100,
                        ax=ax
                    )
                    
                    # Add country labels
                    for _, row in quartile_data.iterrows():
                        ax.annotate(
                            row['Country'],
                            (row['Rail_Network_Trend'], row['Transit_Efficiency_Trend']),
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
                            y='Transit_Efficiency_Trend',
                            scatter=False,
                            color=palette[i],
                            line_kws={'linestyle': '-', 'linewidth': 1.5, 'alpha': 0.7},
                            ax=ax
                        )
            else:
                # Plot all points in one color if no GDP quartiles
                sns.scatterplot(
                    data=efficiency_data,
                    x='Rail_Network_Trend',
                    y='Transit_Efficiency_Trend',
                    s=100,
                    ax=ax
                )
                
                # Add country labels
                for _, row in efficiency_data.iterrows():
                    ax.annotate(
                        row['Country'],
                        (row['Rail_Network_Trend'], row['Transit_Efficiency_Trend']),
                        fontsize=8,
                        alpha=0.7,
                        xytext=(5, 5),
                        textcoords='offset points'
                    )
            
            # Add quadrant lines and labels
            ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
            
            # Add quadrant labels
            ax.text(
                efficiency_data['Rail_Network_Trend'].max() * 0.7,
                efficiency_data['Transit_Efficiency_Trend'].max() * 0.7,
                "Growing rail network\nImproving efficiency",
                ha='center',
                bbox=dict(facecolor='green', alpha=0.1)
            )
            
            ax.text(
                efficiency_data['Rail_Network_Trend'].min() * 0.7,
                efficiency_data['Transit_Efficiency_Trend'].min() * 0.7,
                "Shrinking rail network\nDeclining efficiency",
                ha='center',
                bbox=dict(facecolor='red', alpha=0.1)
            )
            
            # Customize the plot
            ax.set_xlabel('Trend in Rail Network Percentage (Annual Change)', fontsize=12)
            ax.set_ylabel('Trend in Transit Cost Efficiency (Annual Change)', fontsize=12)
            ax.set_title('Relationship Between Rail Network Growth and Transit Cost Efficiency', fontsize=14)
            
            # Calculate correlation
            correlation = efficiency_data['Rail_Network_Trend'].corr(efficiency_data['Transit_Efficiency_Trend'])
            ax.text(
                0.05, 0.95,
                f'Correlation: {correlation:.2f}',
                transform=ax.transAxes,
                fontsize=10,
                bbox=dict(facecolor='white', alpha=0.7)
            )
            
            # Show the legend if GDP quartiles are available
            if 'Unknown' not in efficiency_data['GDP_Quartile'].unique():
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
            - Points in the upper right quadrant show countries with both growing rail networks and improving transit efficiency
            - Points in the lower left quadrant show countries with shrinking rail networks and declining efficiency
            - The correlation coefficient measures the strength of the relationship between rail network growth and efficiency trends
            - Positive correlation supports the hypothesis that expanding rail networks improves transit cost efficiency
            
            This visualization helps identify whether countries that invest in expanding their rail networks 
            achieve better cost efficiency in their national transit systems.
            """)
            
            # Display the data table
            with st.expander("Show Data Table"):
                st.dataframe(efficiency_data[['Country', 'Rail_Network_Trend', 'Transit_Efficiency_Trend', 'GDP_per_capita']])
        else:
            st.warning("Insufficient data to create the Rail Network vs Transit Efficiency visualization.")
    else:
        st.error("Required columns not found for Rail Network vs Transit Efficiency visualization.")