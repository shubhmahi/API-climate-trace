import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ==========================================
# 1. LOAD PARQUET DATA
# ==========================================
try:
    print("Loading Parquet data...")
    df = pd.read_parquet('data/master_data3.parquet', engine='pyarrow')
    print("Data loaded successfully!")
except Exception as e:
    print(f"Error loading parquet: {e}. Please run data_prep.py first.")
    df = pd.DataFrame()

# ==========================================
# 2. APP INITIALIZATION & ATO STYLING
# ==========================================
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "ATO Climate Trace Dashboard"

ATO_FONT = 'TW Cen MT'
ATO_COLORS = ['#4A7EBB', '#E07360', '#F2B14C', '#84B97C', '#283B5E', '#A5A5A5', '#7F60A3', '#48C0B3', '#F2994A']


def apply_ato_layout(fig, x_title=None, y_title=None, is_year=False):
    """Applies clean styling and fixes legend overlap."""
    fig.update_layout(
        font=dict(family=ATO_FONT, color='#333333'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        colorway=ATO_COLORS,
        margin=dict(t=60, b=80, l=60, r=20),
        xaxis=dict(showgrid=False, zeroline=False, showline=True, linecolor='#666666', title=x_title),
        yaxis=dict(showgrid=False, zeroline=False, showline=True, linecolor='#666666', title=y_title),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, bgcolor='rgba(255,255,255,0)'),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family=ATO_FONT),
        title=dict(font=dict(size=18, color='#283B5E'), x=0.02, y=0.95)
    )

    if is_year:
        fig.update_xaxes(dtick=1, tickformat="d")

    return fig


def get_static_options(col_name):
    if col_name in df.columns:
        unique_vals = sorted([x for x in df[col_name].unique() if str(x) not in ['Unknown', 'nan', 'None']])
        return [{'label': str(i).title().replace('_', ' ').replace('-', ' '), 'value': i} for i in unique_vals]
    return []


opts_year = get_static_options('year')
opts_sector = get_static_options('sector')
opts_subsector = get_static_options('subsector')
opts_gas = [{'label': str(i).upper(), 'value': i} for i in
            sorted([x for x in df.get('gas', pd.Series()).unique() if str(x) not in ['Unknown', 'nan']])]
opts_source = get_static_options('sourceType')
opts_country = get_static_options('economy_name')
opts_ato_orig = get_static_options('economy_ato_group_original')
opts_ato_split = get_static_options('economy_ato_group_split')
opts_adb_orig = get_static_options('economy_adb_subregion+original')
opts_adb_split = get_static_options('economy_adb_subregion+split')
opts_income = get_static_options('economy_incomegroup')

# ==========================================
# 3. DASHBOARD LAYOUT
# ==========================================
app.layout = html.Div(
    style={'fontFamily': ATO_FONT, 'backgroundColor': '#F4F5F7', 'minHeight': '100vh', 'display': 'flex',
           'flexDirection': 'column'}, children=[

        html.Div(style={'display': 'flex', 'alignItems': 'center', 'backgroundColor': 'white', 'padding': '15px 30px',
                        'borderBottom': '3px solid #283B5E', 'boxShadow': '0 2px 10px rgba(0,0,0,0.05)',
                        'zIndex': '100'}, children=[
            html.Img(src='assets/ATO LOGO.png', style={'height': '60px', 'marginRight': '25px'}),
            html.H1("Climate Trace Emissions Explorer",
                    style={'color': '#283B5E', 'margin': 0, 'fontSize': '28px', 'fontWeight': 'bold'})
        ]),

        html.Div(style={'display': 'flex', 'flex': '1', 'padding': '20px', 'gap': '20px'}, children=[

            html.Div(style={'width': '320px', 'minWidth': '320px', 'padding': '25px', 'backgroundColor': 'white',
                            'borderRadius': '10px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.05)', 'height': '85vh',
                            'overflowY': 'auto'}, children=[
                html.H3("Core Filters",
                        style={'borderBottom': '2px solid #EEE', 'paddingBottom': '10px', 'color': '#283B5E',
                               'fontSize': '20px'}),

                html.Label("Year:", style={'fontWeight': 'bold', 'marginTop': '10px'}),
                dcc.Dropdown(id='filter-year', options=opts_year, multi=True, placeholder="All Years"),

                html.Label("Sector:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                dcc.Dropdown(id='filter-sector', options=opts_sector, multi=True, placeholder="All Sectors"),

                html.Label("Subsector:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                dcc.Dropdown(id='filter-subsector', options=opts_subsector, multi=True, placeholder="All Subsectors"),

                html.Label("Emission Gas:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                dcc.Dropdown(id='filter-gas', options=opts_gas, multi=True, placeholder="All Gases"),

                html.Label("Source Type:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                dcc.Dropdown(id='filter-source', options=opts_source, multi=True, placeholder="All Sources"),

                html.H3("Economy Filters",
                        style={'borderBottom': '2px solid #EEE', 'paddingBottom': '10px', 'color': '#283B5E',
                               'marginTop': '30px', 'fontSize': '20px'}),

                html.Label("Specific Economy (Country):",
                           style={'fontWeight': 'bold', 'marginTop': '10px', 'color': '#E07360'}),
                dcc.Dropdown(id='filter-country', options=opts_country, placeholder="Select Country to Spin Globe"),

                html.Label("ATO Economy Group Original:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                dcc.Dropdown(id='filter-ato-orig', options=opts_ato_orig, multi=True, placeholder="All"),

                html.Label("ATO Economy Group Split:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                dcc.Dropdown(id='filter-ato-split', options=opts_ato_split, multi=True, placeholder="All"),

                html.Label("ADB Subregion Original:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                dcc.Dropdown(id='filter-adb-orig', options=opts_adb_orig, multi=True, placeholder="All"),

                html.Label("ADB Subregion Split:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                dcc.Dropdown(id='filter-adb-split', options=opts_adb_split, multi=True, placeholder="All"),

                html.Label("Income Group:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                dcc.Dropdown(id='filter-income', options=opts_income, multi=True, placeholder="All"),
            ]),

            html.Div(style={'flex': '1', 'minWidth': '0'}, children=[
                dcc.Loading(
                    id="loading-tabs", type="circle", color=ATO_COLORS[0],
                    children=[
                        dcc.Tabs(id="tabs", style={'fontFamily': ATO_FONT}, children=[

                            dcc.Tab(label='Geospatial Overview', style={'fontWeight': 'bold'},
                                    selected_style={'fontWeight': 'bold', 'borderTop': f'3px solid {ATO_COLORS[0]}'},
                                    children=[
                                        html.Div(
                                            style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px',
                                                   'marginTop': '20px'}, children=[
                                                html.Div(dcc.Graph(id='chart-globe', style={'height': '600px'}),
                                                         style={'gridColumn': '1 / -1', 'backgroundColor': 'white',
                                                                'padding': '15px', 'borderRadius': '10px',
                                                                'boxShadow': '0 2px 10px rgba(0,0,0,0.05)'}),
                                                html.Div(dcc.Graph(id='chart-source-type', style={'height': '420px'}),
                                                         style={'backgroundColor': 'white', 'padding': '15px',
                                                                'borderRadius': '10px',
                                                                'boxShadow': '0 2px 10px rgba(0,0,0,0.05)'}),
                                                html.Div(dcc.Graph(id='chart-top-countries', style={'height': '420px'}),
                                                         style={'backgroundColor': 'white', 'padding': '15px',
                                                                'borderRadius': '10px',
                                                                'boxShadow': '0 2px 10px rgba(0,0,0,0.05)'}),
                                            ])
                                    ]),

                            dcc.Tab(label='Sector & Economic Analysis', style={'fontWeight': 'bold'},
                                    selected_style={'fontWeight': 'bold', 'borderTop': f'3px solid {ATO_COLORS[0]}'},
                                    children=[
                                        html.Div(
                                            style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px',
                                                   'marginTop': '20px'}, children=[
                                                html.Div(
                                                    dcc.Graph(id='chart-ato-comparison', style={'height': '500px'}),
                                                    style={'gridColumn': '1 / -1', 'backgroundColor': 'white',
                                                           'padding': '15px', 'borderRadius': '10px',
                                                           'boxShadow': '0 2px 10px rgba(0,0,0,0.05)'}),
                                                html.Div(dcc.Graph(id='chart-sector-pie', style={'height': '420px'}),
                                                         style={'backgroundColor': 'white', 'padding': '15px',
                                                                'borderRadius': '10px',
                                                                'boxShadow': '0 2px 10px rgba(0,0,0,0.05)'}),
                                                html.Div(dcc.Graph(id='chart-income-bar', style={'height': '420px'}),
                                                         style={'backgroundColor': 'white', 'padding': '15px',
                                                                'borderRadius': '10px',
                                                                'boxShadow': '0 2px 10px rgba(0,0,0,0.05)'}),
                                                html.Div(
                                                    dcc.Graph(id='chart-subregion-tree', style={'height': '500px'}),
                                                    style={'gridColumn': '1 / -1', 'backgroundColor': 'white',
                                                           'padding': '15px', 'borderRadius': '10px',
                                                           'boxShadow': '0 2px 10px rgba(0,0,0,0.05)'}),
                                            ])
                                    ]),

                            dcc.Tab(label='Deep Dive & Facilities', style={'fontWeight': 'bold'},
                                    selected_style={'fontWeight': 'bold', 'borderTop': f'3px solid {ATO_COLORS[0]}'},
                                    children=[
                                        html.Div(
                                            style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px',
                                                   'marginTop': '20px'}, children=[
                                                html.Div(dcc.Graph(id='chart-flat-map', style={'height': '600px'}),
                                                         style={'gridColumn': '1 / -1', 'backgroundColor': 'white',
                                                                'padding': '15px', 'borderRadius': '10px',
                                                                'boxShadow': '0 2px 10px rgba(0,0,0,0.05)'}),
                                                html.Div(dcc.Graph(id='chart-gas-comp', style={'height': '420px'}),
                                                         style={'backgroundColor': 'white', 'padding': '15px',
                                                                'borderRadius': '10px',
                                                                'boxShadow': '0 2px 10px rgba(0,0,0,0.05)'}),
                                                html.Div(dcc.Graph(id='chart-box-plot', style={'height': '420px'}),
                                                         style={'backgroundColor': 'white', 'padding': '15px',
                                                                'borderRadius': '10px',
                                                                'boxShadow': '0 2px 10px rgba(0,0,0,0.05)'}),
                                            ])
                                    ])
                        ])
                    ]
                )
            ])
        ])
    ])


# ==========================================
# 4. CHARTS CALLBACK
# ==========================================
@app.callback(
    [Output('chart-globe', 'figure'),
     Output('chart-source-type', 'figure'),
     Output('chart-top-countries', 'figure'),
     Output('chart-ato-comparison', 'figure'),
     Output('chart-sector-pie', 'figure'),
     Output('chart-income-bar', 'figure'),
     Output('chart-subregion-tree', 'figure'),
     Output('chart-flat-map', 'figure'),
     Output('chart-gas-comp', 'figure'),
     Output('chart-box-plot', 'figure')],
    [Input('filter-year', 'value'), Input('filter-sector', 'value'), Input('filter-subsector', 'value'),
     Input('filter-gas', 'value'), Input('filter-source', 'value'), Input('filter-country', 'value'),
     Input('filter-ato-orig', 'value'), Input('filter-ato-split', 'value'),
     Input('filter-adb-orig', 'value'), Input('filter-adb-split', 'value'), Input('filter-income', 'value')]
)
def update_charts(years, sectors, subsectors, gases, sources, specific_country, ato_orig, ato_split, adb_orig,
                  adb_split, incomes):
    filtered_df = df.copy()
    val_col = 'emissionsQuantity' if 'emissionsQuantity' in filtered_df.columns else None

    if not val_col or filtered_df.empty:
        empty = go.Figure().add_annotation(text="No Data Available", showarrow=False,
                                           font=dict(size=20, color='#A5A5A5'))
        empty.update_layout(plot_bgcolor='white', paper_bgcolor='white', xaxis=dict(visible=False),
                            yaxis=dict(visible=False))
        return [empty] * 10

    # Apply Filters to Data
    if years: filtered_df = filtered_df[filtered_df['year'].isin(years)]
    if sectors: filtered_df = filtered_df[filtered_df['sector'].isin(sectors)]
    if subsectors: filtered_df = filtered_df[filtered_df['subsector'].isin(subsectors)]
    if gases: filtered_df = filtered_df[filtered_df['gas'].isin(gases)]
    if sources: filtered_df = filtered_df[filtered_df['sourceType'].isin(sources)]
    if ato_orig: filtered_df = filtered_df[filtered_df['economy_ato_group_original'].isin(ato_orig)]
    if ato_split: filtered_df = filtered_df[filtered_df['economy_ato_group_split'].isin(ato_split)]
    if adb_orig: filtered_df = filtered_df[filtered_df['economy_adb_subregion+original'].isin(adb_orig)]
    if adb_split: filtered_df = filtered_df[filtered_df['economy_adb_subregion+split'].isin(adb_split)]
    if incomes: filtered_df = filtered_df[filtered_df['economy_incomegroup'].isin(incomes)]

    center_lat, center_lon = 20, 80
    if specific_country:
        filtered_df = filtered_df[filtered_df['economy_name'] == specific_country]
        if not filtered_df.empty and 'lat' in filtered_df.columns:
            center_lat, center_lon = filtered_df['lat'].mean(), filtered_df['lon'].mean()

    map_sample_limit = 8000
    map_df = filtered_df.sample(n=min(len(filtered_df), map_sample_limit)) if len(
        filtered_df) > map_sample_limit else filtered_df

    # SMART TOOLTIP LOGIC (Strict error checking for 0 and license restricted)
    def is_valid_metric(val):
        if pd.isna(val): return False
        val_str = str(val).strip().lower()
        if val_str in ['0', '0.0', 'nan', 'none', 'unknown', 'license restricted']: return False
        return True

    def create_hover_text(df_row):
        text = f"<b>Economy:</b> {df_row.get('economy_name', 'Unknown')}<br>"
        text += f"<b>Sector:</b> {str(df_row.get('sector', '')).title()}<br>"
        text += f"<b>Subsector:</b> {str(df_row.get('subsector', '')).title()}<br>"

        if is_valid_metric(df_row.get('sourceType')):
            text += f"<b>Source Type:</b> {str(df_row['sourceType']).title()}<br>"
        if is_valid_metric(df_row.get('assetType')):
            text += f"<b>Asset Type:</b> {str(df_row['assetType']).title()}<br>"

        text += f"<b>Emissions:</b> {float(df_row.get('emissionsQuantity', 0)):,.2f} Tonnes"

        if 'capacity' in df_row and is_valid_metric(df_row['capacity']):
            text += f"<br><b>Capacity:</b> {float(df_row['capacity']):,.2f} {df_row.get('capacityUnits', '')}"

        if 'activity' in df_row and is_valid_metric(df_row['activity']):
            text += f"<br><b>Activity:</b> {float(df_row['activity']):,.2f} {df_row.get('activityUnits', '')}"

        if 'emissionsFactor' in df_row and is_valid_metric(df_row['emissionsFactor']):
            text += f"<br><b>EF:</b> {float(df_row['emissionsFactor']):,.4f} {df_row.get('emissionsFactorUnits', '')}"

        return text

    if not map_df.empty:
        map_df['hover_info'] = map_df.apply(create_hover_text, axis=1)
    else:
        map_df['hover_info'] = ""

    # 1. Globe
    fig_globe = go.Figure()
    if 'lon' in map_df.columns and 'lat' in map_df.columns:
        fig_globe.add_trace(go.Scattergeo(
            lon=map_df['lon'], lat=map_df['lat'],
            marker=dict(size=4, color=ATO_COLORS[0], opacity=0.8, line=dict(width=0)),
            mode='markers', hoverinfo='text', text=map_df['hover_info']
        ))
    fig_globe.update_layout(
        title=dict(text="Global Asset Locations", font=dict(size=18, color='#283B5E'), x=0.02, y=0.95),
        geo=dict(projection_type='orthographic', showland=True, landcolor="#F4F5F7", showcountries=False,
                 showocean=True, oceancolor="white", projection_rotation=dict(lon=center_lon, lat=center_lat, roll=0)),
        margin={"r": 0, "t": 50, "l": 0, "b": 0}, font=dict(family=ATO_FONT)
    )

    # 2. Source Type Donut (Fixed the wrong comparison issue)
    if 'sourceType' in filtered_df.columns:
        source_df = filtered_df.groupby('sourceType', observed=True)[val_col].sum().reset_index()
        fig_source = px.pie(source_df, names='sourceType', values=val_col, title="Emissions by Source Type", hole=0.5,
                            color_discrete_sequence=[ATO_COLORS[2], ATO_COLORS[1]])
        fig_source.update_traces(textposition='inside', textinfo='percent+label')
        fig_source.update_layout(font=dict(family=ATO_FONT), margin=dict(t=60, b=30, l=30, r=30),
                                 title=dict(font=dict(size=18, color='#283B5E'), x=0.02, y=0.95))
    else:
        fig_source = go.Figure()

    # 3. Top 10 Countries
    top_c = filtered_df.groupby('economy_name', observed=True)[val_col].sum().nlargest(10).reset_index()
    fig_top = px.bar(top_c, y='economy_name', x=val_col, orientation='h', title="Top 10 Emitting Economies")
    fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
    fig_top = apply_ato_layout(fig_top, x_title="Emissions (Tonnes)", y_title="Economy")

    # 4. ATO Stacked Bar
    if 'year' in filtered_df.columns:
        ato_df = filtered_df.groupby(['year', 'economy_ato_group_original'], observed=True)[val_col].sum().reset_index()
        fig_ato = px.bar(ato_df, x='year', y=val_col, color='economy_ato_group_original',
                         title="Emission Trends by ATO Grouping", barmode='stack')
        fig_ato = apply_ato_layout(fig_ato, x_title="Year", y_title="Emissions (Tonnes)", is_year=True)
    else:
        fig_ato = go.Figure()

    # 5. Sector Pie
    if 'sector' in filtered_df.columns:
        sec_df = filtered_df.groupby('sector', observed=True)[val_col].sum().reset_index()
        fig_sec = px.pie(sec_df, names='sector', values=val_col, title="Sectoral Contribution", hole=0.5,
                         color_discrete_sequence=ATO_COLORS)
        fig_sec.update_traces(textposition='inside', textinfo='percent+label')
        fig_sec.update_layout(font=dict(family=ATO_FONT), margin=dict(t=60, b=30, l=30, r=30),
                              title=dict(font=dict(size=18, color='#283B5E'), x=0.02, y=0.95))
    else:
        fig_sec = go.Figure()

    # 6. Income Group
    if 'economy_incomegroup' in filtered_df.columns:
        inc_df = filtered_df.groupby('economy_incomegroup', observed=True)[val_col].sum().reset_index()
        fig_inc = apply_ato_layout(px.bar(inc_df, x='economy_incomegroup', y=val_col, title="Emissions by Income Group",
                                          color_discrete_sequence=[ATO_COLORS[3]]), x_title="Income Group",
                                   y_title="Emissions (Tonnes)")
    else:
        fig_inc = go.Figure()

    # 7. Subregion Treemap
    if 'economy_region' in filtered_df.columns and 'economy_name' in filtered_df.columns:
        tree_df = filtered_df.groupby(['economy_region', 'economy_name'], observed=True)[val_col].sum().reset_index()
        tree_df = tree_df[tree_df[val_col] > 0]
        fig_tree = px.treemap(tree_df, path=['economy_region', 'economy_name'], values=val_col,
                              title="Regional Breakdown to Economy Level")
        fig_tree.update_traces(hovertemplate='<b>%{label}</b><br>Emissions: %{value:,.0f} Tonnes<extra></extra>')
        fig_tree.update_layout(font=dict(family=ATO_FONT), margin=dict(t=60, b=10, l=10, r=10), colorway=ATO_COLORS,
                               title=dict(font=dict(size=18, color='#283B5E'), x=0.02, y=0.95))
    else:
        fig_tree = go.Figure()

    # 8. Detailed Flat Map
    if 'lon' in map_df.columns and 'lat' in map_df.columns:
        fig_flat = px.scatter_geo(map_df, lat="lat", lon="lon", color="sector" if 'sector' in map_df.columns else None,
                                  title="Asset Level Detail Map", custom_data=['hover_info'])
        fig_flat.update_traces(marker=dict(size=4, opacity=0.7), hovertemplate="%{customdata[0]}")
        fig_flat.update_layout(geo=dict(showland=True, landcolor="#F4F5F7", showcountries=False),
                               font=dict(family=ATO_FONT), margin={"r": 0, "t": 60, "l": 0, "b": 80},
                               legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
                               title=dict(font=dict(size=18, color='#283B5E'), x=0.02, y=0.95))
    else:
        fig_flat = go.Figure()

    # 9. Gas Composition
    if 'gas' in filtered_df.columns:
        gas_df = filtered_df.groupby('gas', observed=True)[val_col].sum().reset_index()
        fig_gas = apply_ato_layout(
            px.bar(gas_df, x='gas', y=val_col, title="Volume by Gas Type", color_discrete_sequence=[ATO_COLORS[4]]),
            x_title="Gas Type", y_title="Emissions (Tonnes)")
    else:
        fig_gas = go.Figure()

    # 10. Box Plot
    if 'economy_ato_group_original' in filtered_df.columns:
        box_df = filtered_df.sample(n=min(len(filtered_df), 50000)) if len(filtered_df) > 50000 else filtered_df
        fig_box = px.box(box_df, x='economy_ato_group_original', y=val_col, title="Emission Distribution by ATO Group",
                         color_discrete_sequence=[ATO_COLORS[0]])
        fig_box = apply_ato_layout(fig_box, x_title="ATO Group", y_title="Emissions (Log Scale)")
        fig_box.update_yaxes(type="log")
    else:
        fig_box = go.Figure()

    return fig_globe, fig_source, fig_top, fig_ato, fig_sec, fig_inc, fig_tree, fig_flat, fig_gas, fig_box


if __name__ == '__main__':
    app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
    server = app.server
  # app.run(debug=True, port=8050)