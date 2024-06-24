import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Generate dummy data
np.random.seed(42)
dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq='M')
products = ['Pet Food', 'Confectionary', 'Other Food Product']

data = {
    'Product': np.random.choice(products, len(dates)),
    'Date': dates,
    'Sales': np.random.randint(10000, 50000, len(dates)),
    'Paid_Search_Spend': np.random.randint(500, 5000, len(dates)),
    'Banner_Ads_Spend': np.random.randint(300, 3000, len(dates)),
    'Impressions_Paid_Search': np.random.randint(10000, 50000, len(dates)),
    'Impressions_Banner_Ads': np.random.randint(8000, 40000, len(dates)),
    'Clicks_Paid_Search': np.random.randint(500, 5000, len(dates)),
    'Clicks_Banner_Ads': np.random.randint(300, 3000, len(dates)),
    'Conversions_Paid_Search': np.random.randint(50, 500, len(dates)),
    'Conversions_Banner_Ads': np.random.randint(30, 300, len(dates)),
    'Customer_Loyalty': np.random.uniform(0, 1, len(dates)),
    'Perfect_Store_Score': np.random.uniform(0, 1, len(dates))
}

df = pd.DataFrame(data)

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Marketing Mix Modeling Dashboard"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Label("Select Objective"),
            dcc.Dropdown(
                id='objective-dropdown',
                options=[
                    {'label': 'ROI', 'value': 'ROI'},
                    {'label': 'Revenue', 'value': 'Revenue'},
                    {'label': 'Sales', 'value': 'Sales'}
                ],
                value='Sales'
            ),
        ], width=2),
        dbc.Col([
            dbc.Label("Select Product"),
            dcc.Dropdown(
                id='product-dropdown',
                options=[{'label': prod, 'value': prod} for prod in products],
                value=products,
                multi=True
            ),
        ], width=2),
        dbc.Col([
            dbc.Label("Budget Threshold"),
            dcc.Input(id='budget-input', type='number', value=1000)
        ], width=2),
        dbc.Col([
            dbc.Label("Alpha"),
            dcc.Slider(id='alpha-slider', min=0.01, max=1.0, step=0.01, value=0.5)
        ], width=2),
        dbc.Col([
            dbc.Label("Beta"),
            dcc.Slider(id='beta-slider', min=0.01, max=1.0, step=0.01, value=0.5)
        ], width=2),
        dbc.Col([
            dbc.Label("Date Range"),
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date=df['Date'].min(),
                end_date=df['Date'].max()
            )
        ], width=2),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='adstock-graph'), width=6),
        dbc.Col(dcc.Graph(id='diminishing-graph'), width=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='sales-ad-spend-graph'), width=12),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='budget-product-graph'), width=6),
        dbc.Col(dcc.Graph(id='budget-ad-graph'), width=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='uplift-graph'), width=12),
    ])
], fluid=True)

# Callback to update graphs based on inputs
@app.callback(
    [Output('adstock-graph', 'figure'),
     Output('diminishing-graph', 'figure'),
     Output('sales-ad-spend-graph', 'figure'),
     Output('budget-product-graph', 'figure'),
     Output('budget-ad-graph', 'figure'),
     Output('uplift-graph', 'figure')],
    [Input('objective-dropdown', 'value'),
     Input('product-dropdown', 'value'),
     Input('budget-input', 'value'),
     Input('alpha-slider', 'value'),
     Input('beta-slider', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_graphs(objective, selected_products, budget_threshold, alpha, beta, start_date, end_date):
    filtered_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    filtered_df = filtered_df[filtered_df['Product'].isin(selected_products)]
    filtered_df = filtered_df[(filtered_df['Paid_Search_Spend'] + filtered_df['Banner_Ads_Spend']) >= budget_threshold]
    
    # Adstock calculation
    def adstock(series, alpha, beta):
        result = [series.iloc[0]]
        for i in range(1, len(series)):
            result.append(series.iloc[i] + alpha * result[i-1] * beta)
        return result

    filtered_df['Adstock_Paid_Search'] = adstock(filtered_df['Paid_Search_Spend'], alpha, beta)
    filtered_df['Adstock_Banner_Ads'] = adstock(filtered_df['Banner_Ads_Spend'], alpha, beta)

    # Diminishing returns
    filtered_df['Diminishing_Paid_Search'] = filtered_df['Paid_Search_Spend'] ** alpha
    filtered_df['Diminishing_Banner_Ads'] = filtered_df['Banner_Ads_Spend'] ** beta

    # Adstock graph
    fig_adstock = go.Figure()
    fig_adstock.add_trace(go.Bar(x=filtered_df['Date'], y=filtered_df['Paid_Search_Spend'], name='Initial Advertising (Paid Search)', marker_color='lightgreen'))
    fig_adstock.add_trace(go.Bar(x=filtered_df['Date'], y=filtered_df['Banner_Ads_Spend'], name='Initial Advertising (Banner Ads)', marker_color='lightblue'))
    fig_adstock.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Adstock_Paid_Search'], mode='lines', name='Adstocked Advertising (Paid Search)', line=dict(color='green', width=2)))
    fig_adstock.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Adstock_Banner_Ads'], mode='lines', name='Adstocked Advertising (Banner Ads)', line=dict(color='blue', width=2)))

    fig_adstock.update_layout(barmode='overlay')
    fig_adstock.update_traces(opacity=0.6)
    fig_adstock.update_layout(title='Adstock Effect Over Time', xaxis_title='Date', yaxis_title='Ad Spend', legend_title='Legend')

    # Diminishing returns graph
    fig_diminishing = go.Figure()
    fig_diminishing.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Diminishing_Paid_Search'], mode='lines', name='Diminishing Paid Search', line=dict(color='green', width=2)))
    fig_diminishing.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Diminishing_Banner_Ads'], mode='lines', name='Diminishing Banner Ads', line=dict(color='blue', width=2)))

    fig_diminishing.update_layout(title='Diminishing Returns Over Time', xaxis_title='Date', yaxis_title='Spend', legend_title='Legend')

    # Sales and Ad Spend graph
    fig_sales_ad = go.Figure()
    fig_sales_ad.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Sales'], mode='lines', name='Sales', line=dict(color='black', width=2)))
    fig_sales_ad.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Paid_Search_Spend'], mode='lines', name='Paid Search Spend', line=dict(color='green', width=2)))
    fig_sales_ad.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Banner_Ads_Spend'], mode='lines', name='Banner Ads Spend', line=dict(color='blue', width=2)))

    fig_sales_ad.update_layout(title='Sales and Advertising Spend Over Time', xaxis_title='Date', yaxis_title='Value', legend_title='Legend')

    # Budget distribution by product
    fig_budget_product = px.line(filtered_df, x='Date', y=['Paid_Search_Spend', 'Banner_Ads_Spend'], color='Product')

    fig_budget_product.update_layout(title='Budget Distribution by Product', xaxis_title='Date', yaxis_title='Spend', legend_title='Product')

    # Budget distribution between ad types
    fig_budget_ad = go.Figure()
    fig_budget_ad.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Paid_Search_Spend'], mode='lines', name='Paid Search Spend', line=dict(color='green', width=2)))
    fig_budget_ad.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Banner_Ads_Spend'], mode='lines', name='Banner Ads Spend', line=dict(color='blue', width=2)))

    fig_budget_ad.update_layout(title='Budget Distribution Between Ad Types', xaxis_title='Date', yaxis_title='Spend', legend_title='Legend')

    # Uplift graph
    fig_uplift = go.Figure()
    fig_uplift.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Sales'], mode='lines', name='Actual Sales', line=dict(color='black', width=2)))
    fig_uplift.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Sales'] * (1 + alpha), mode='lines', name='Uplifted Sales', line=dict(color='red', width=2, dash='dash')))

    fig_uplift.update_layout(title='Uplift in Sales Over Time', xaxis_title='Date', yaxis_title='Sales', legend_title='Legend')

    return fig_adstock, fig_diminishing, fig_sales_ad, fig_budget_product, fig_budget_ad, fig_uplift

if __name__ == '__main__':
    app.run_server(debug=True)
