import dash
from dash import Dash, dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime


# Converts CSV data into a Pandas DataFrame
df = pd.read_csv('dummynumbers.csv')
df["Date"] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

# style.css defines the styling of the app
app = dash.Dash(__name__, external_stylesheets=['style.css']) #Initialise app

def get_weather_data(lat, lon, start_date, end_date):
    pass

def create_weather_graph(df, title):
    pass

def geocode_location(search_term):
    pass


#api_key = '866e741f879a137905380bc68d323f5d'

@app.callback(
    Output('weather-graph', 'figure'),
    Input('location-dropdown', 'value'),
    Input('date-range-picker', 'start_date'),
    Input('date-range-picker', 'end_date')
)
def update_graph(selected_locations, start_date, end_date):
    pass


@app.callback(
    Output('location-dropdown', 'options'),
    Output('location-dropdown', 'value'),
    Input('location-search', 'value'),
    State('location-dropdown', 'value')
)
def update_location_options(search_term, selected_locations):
    pass


#fig = px.line(filtered_df, x='Date', y='Peak Temp (ºC)', color='Location', title='Historical Temperature Comparison')
    #return fig


# Defines the structure and content of app's UI
app.layout = html.Div(className='container', children=[
    html.H1("Weather Data Visualisation"),
    dcc.Input(id='location-search', placeholder='Enter a location', type='text'),
    dcc.Dropdown(
        id='location-dropdown',
        options=[{'label': loc, 'value': loc} for loc in df['Location'].unique()],
        value=df['Location'].unique(),
        multi=True,
        className='dropdown'
    ),
    dcc.DatePickerRange(
        id='date-range-picker',
        min_date_allowed=df["Date"].min(),
        max_date_allowed=df["Date"].max(),
        start_date=df['Date'].min(),
        end_date=df['Date'].max()

    ),
    dcc.Graph(id='weather-graph', className='graph')
]) #Passes Plotly figure to the dcc.Graph component




if __name__ == '__main__':
    app.run_server(debug=True)