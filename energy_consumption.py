import pandas as pd
from dash import dcc, html, dash_table, Input, Output
import dash
import plotly.express as px
from scipy import stats

df = pd.read_csv('energy_consumption.csv')

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Sorting Algorithm Energy Consumption Dashboard", style={'text-align': 'center'}),
    dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.head(10).to_dict('records'),
        page_size=10
    ),
    html.Label("Select Input Size:", style={'margin-top': '20px'}),
    dcc.Dropdown(
        id='input-size-dropdown',
        options=[{'label': size, 'value': size} for size in df['Input_Size'].unique()],
        value='Small'
    ),
    dcc.Graph(id='energy-graph', style={'margin-top': '20px'}),
    html.Div(id='anova-result', style={'margin-top': '20px'}),
    
    # Added spacing for ANOVA calculator
    html.Div(style={'margin-top': '40px'}),
    
    html.H3("ANOVA Calculator", style={'text-align': 'center'}),
    html.Div([
        html.Label("Input Size:", style={'margin-top': '20px'}),
        dcc.Dropdown(
            id='anova-input-size-dropdown',
            options=[{'label': size, 'value': size} for size in df['Input_Size'].unique()],
            value='Small'
        ),
    ], style={'margin-bottom': '20px'}),
    
    html.Div(id='anova-output', style={'margin-top': '20px'}),
    dash_table.DataTable(
        id='anova-table',
        columns=[
            {'name': 'Source of Variation', 'id': 'source'},
            {'name': 'Sum of Squares', 'id': 'ss'},
            {'name': 'Degree of Freedom', 'id': 'df'},
            {'name': 'Mean Square', 'id': 'ms'},
            {'name': 'F', 'id': 'f'},
        ],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
        },
        style_header={
            'backgroundColor': 'lightgrey',
            'fontWeight': 'bold'
        },
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto'
        }
    ),

    # Generalized ANOVA Calculator Section
    html.Div(style={'margin-top': '60px'}),
    html.H3("Generalized ANOVA Calculator", style={'text-align': 'center'}),
    html.Div([
        html.Label("Input Values for Group 1 (comma separated):", style={'margin-top': '20px'}),
        dcc.Input(id='group1-input', type='text', placeholder='e.g., 5,6,7,8,9', style={'width': '100%', 'margin-bottom': '20px'}),
        html.Label("Input Values for Group 2 (comma separated):", style={'margin-top': '20px'}),
        dcc.Input(id='group2-input', type='text', placeholder='e.g., 3,4,5,2,6', style={'width': '100%', 'margin-bottom': '20px'}),
        html.Label("Input Values for Group 3 (comma separated):", style={'margin-top': '20px'}),
        dcc.Input(id='group3-input', type='text', placeholder='e.g., 8,7,9,6,10', style={'width': '100%', 'margin-bottom': '20px'}),
        html.Button("Calculate ANOVA", id='general-anova-button', n_clicks=0, style={'margin-top': '10px'}),
    ], style={'margin-bottom': '20px'}),
    
    dash_table.DataTable(
        id='general-anova-table',
        columns=[
            {'name': 'Source of Variation', 'id': 'source'},
            {'name': 'Sum of Squares', 'id': 'ss'},
            {'name': 'Degree of Freedom', 'id': 'df'},
            {'name': 'Mean Square', 'id': 'ms'},
            {'name': 'F', 'id': 'f'},
        ],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
        },
        style_header={
            'backgroundColor': 'lightgrey',
            'fontWeight': 'bold'
        },
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto'
        }
    ),
    
    html.Div(id='general-anova-output', style={'margin-top': '20px'}),
])

@app.callback(
    Output('energy-graph', 'figure'),
    Output('anova-result', 'children'),
    Input('input-size-dropdown', 'value')
)
def update_graph(input_size):
    filtered_df = df[df['Input_Size'] == input_size]
    fig = px.bar(filtered_df, x='Algorithm', y='Energy_Consumption', color='Algorithm',
                 title=f"Energy Consumption for Input Size: {input_size}")

    algorithms = filtered_df['Algorithm'].unique()
    anova_results = []
    
    for algorithm in algorithms:
        energy_values = filtered_df[filtered_df['Algorithm'] == algorithm]['Energy_Consumption']
        anova_results.append(energy_values)

    anova_result = stats.f_oneway(*anova_results)

    result_text = (
        f"ANOVA Results:\n"
        f"F-Statistic: {anova_result.statistic:.2f}\n"
        f"P-Value: {anova_result.pvalue:.4f}\n"
    )
    if anova_result.pvalue < 0.05:
        result_text += "There is a significant difference in energy consumption among the algorithms."
    else:
        result_text += "No significant difference in energy consumption among the algorithms."

    return fig, result_text

@app.callback(
    Output('anova-output', 'children'),
    Output('anova-table', 'data'),
    Input('anova-input-size-dropdown', 'value')
)
def calculate_anova(anova_input_size):
    filtered_df = df[df['Input_Size'] == anova_input_size]
    groups = [filtered_df[filtered_df['Algorithm'] == algo]['Energy_Consumption'] for algo in filtered_df['Algorithm'].unique()]

    # ANOVA calculations
    n_total = len(filtered_df)
    grand_mean = filtered_df['Energy_Consumption'].mean()
    
    ss_total = sum((filtered_df['Energy_Consumption'] - grand_mean) ** 2)

    ss_between = sum(len(group) * (group.mean() - grand_mean) ** 2 for group in groups)
    ss_within = sum(((group - group.mean()) ** 2).sum() for group in groups)

    df_between = len(groups) - 1
    df_within = n_total - len(groups)

    ms_between = ss_between / df_between if df_between > 0 else 0
    ms_within = ss_within / df_within if df_within > 0 else 0

    f_statistic = ms_between / ms_within if ms_within > 0 else 0

    # Create a table of results
    anova_table = [
        {'source': 'Between Groups', 'ss': ss_between, 'df': df_between, 'ms': ms_between, 'f': f_statistic},
        {'source': 'Within Groups', 'ss': ss_within, 'df': df_within, 'ms': ms_within, 'f': None},
        {'source': 'Total', 'ss': ss_total, 'df': n_total - 1, 'ms': None, 'f': None},
    ]

    critical_value = stats.f.ppf(0.95, df_between, df_within)
    decision = "Reject the null hypothesis." if f_statistic > critical_value else "Fail to reject the null hypothesis."
    
    conclusion = f"F-Statistic: {f_statistic:.2f}, Critical Value: {critical_value:.2f}."
    
    return conclusion + " Decision: " + decision, anova_table

@app.callback(
    Output('general-anova-output', 'children'),
    Output('general-anova-table', 'data'),
    Input('general-anova-button', 'n_clicks'),
    Input('group1-input', 'value'),
    Input('group2-input', 'value'),
    Input('group3-input', 'value')
)
def calculate_generalized_anova(n_clicks, group1, group2, group3):
    if n_clicks > 0:
        # Convert inputs to lists of floats
        try:
            group1_values = [float(x) for x in group1.split(',') if x.strip()]
            group2_values = [float(x) for x in group2.split(',') if x.strip()]
            group3_values = [float(x) for x in group3.split(',') if x.strip()]
        except ValueError:
            return "Please enter valid numeric values.", []

        groups = [group1_values, group2_values, group3_values]

        # ANOVA calculations
        n_total = sum(len(group) for group in groups)
        grand_mean = sum(sum(group) for group in groups) / n_total

        ss_total = sum((value - grand_mean) ** 2 for group in groups for value in group)

        ss_between = sum(len(group) * (sum(group) / len(group) - grand_mean) ** 2 for group in groups)
        ss_within = sum(sum((value - (sum(group) / len(group))) ** 2 for value in group) for group in groups)

        df_between = len(groups) - 1
        df_within = n_total - len(groups)

        ms_between = ss_between / df_between if df_between > 0 else 0
        ms_within = ss_within / df_within if df_within > 0 else 0

        f_statistic = ms_between / ms_within if ms_within > 0 else 0

        # Create a table of results
        general_anova_table = [
            {'source': 'Between Groups', 'ss': ss_between, 'df': df_between, 'ms': ms_between, 'f': f_statistic},
            {'source': 'Within Groups', 'ss': ss_within, 'df': df_within, 'ms': ms_within, 'f': None},
            {'source': 'Total', 'ss': ss_total, 'df': n_total - 1, 'ms': None, 'f': None},
        ]

        critical_value = stats.f.ppf(0.95, df_between, df_within)
        decision = "Reject the null hypothesis." if f_statistic > critical_value else "Fail to reject the null hypothesis."

        conclusion = f"F-Statistic: {f_statistic:.2f}, Critical Value: {critical_value:.2f}."

        return f"{conclusion} Decision: {decision}", general_anova_table

    return "", []

if __name__ == '__main__':
    app.run_server(debug=True)
