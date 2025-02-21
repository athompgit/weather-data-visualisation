import dash
from dash import Dash, dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import requests_cache
from retry_requests import retry
import json
import openmeteo_requests
from datetime import datetime, timedelta, date



def get_weather_data(lat, lon, start_date, end_date):

    meteo_url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'hourly': 'temperature_2m',
        'timezone': 'auto'
    }
    try:
        response = requests.get(meteo_url, params=params)
        response.raise_for_status()
        data = response.json()

        hourly = data.get('hourly', {})
        times = hourly.get('time', [])
        temps = hourly.get('temperature_2m', [])

        if not times or not temps:
            print("No hourly data returned.")
            return pd.DataFrame()

        meteo_df = pd.DataFrame({
            'time': pd.to_datetime(times),
            'temperature_2m': temps
        })

        return meteo_df

    except Exception as e:
        print(f"Error fetching data from Open-Meteo: {e}")
        return pd.DataFrame()

def create_weather_graph(meteo_df, title):
    if meteo_df.empty:
        return go.Figure(data=[go.Scatter()], layout=go.Layout(title=title, xaxis=dict(title='Time'), yaxis=dict(title='Temperature')))
    fig = px.line(meteo_df, x='time', y='temperature_2m', title=title)
    return fig

def geocode_location(search_term):
    if not search_term:
        return None, None

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={search_term}&count=5"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data and 'results' in data:
            for result in data['results']:
                if 'latitude' in result and 'longitude' in result:
                    latitude = result['latitude']
                    longitude = result['longitude']
                    return latitude, longitude

        else:
            print(f"No results for '{search_term}'.")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"Geocoding Error: {e}")
        return None, None
    except (KeyError, TypeError) as e:
        print(f"Error parsing geocoding data: {e}")
        return None, None


#Dash App setup

app = dash.Dash(__name__, external_stylesheets=['style.css']) #Initialise app

initial_dropdown_options = []

today = date.today()
min_date = today - timedelta(days=1000)


# Defines the structure and content of app's UI
app.layout = html.Div(className='container', children=[
    html.H1("Weather Data Visualisation"),
    dcc.Input(id='location-search', placeholder='Enter a location', type='text'),
    dcc.Dropdown(
        id='location-dropdown',
        options=initial_dropdown_options,
        value=None,
        multi=True,
        className='dropdown'
    ),
    dcc.DatePickerRange(
        id='date-range-picker',
        min_date_allowed=min_date,
        max_date_allowed=today,
        start_date=min_date,
        end_date=today

    ),
    dcc.Graph(id='weather-graph', className='graph')
]) #Passes Plotly figure to the dcc.Graph component


@app.callback(
    Output('weather-graph', 'figure'),
    Input('location-dropdown', 'value'),
    Input('date-range-picker', 'start_date'),
    Input('date-range-picker', 'end_date')
)
def update_graph(selected_locations, start_date, end_date):
  #  historical_url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    if not selected_locations:
        return dash.no_update

    fig = go.Figure()


    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

    for location in selected_locations:
        try:
            lat, lon = map(float, location.split(','))
        except ValueError:
            print(f"Invalid location format: {location}")
            continue

        meteo_df = get_weather_data(lat, lon, start_date_obj, end_date_obj)

        if not meteo_df.empty:
            temp_fig = create_weather_graph(meteo_df, f"Temperature at {location}")
        else:
            print(f"No available data to display for {location}")

    fig.update_layout(title="Historical Weather Comparison", xaxis_title="Time", yaxis_title="Temperature (ºC)")

    return fig


@app.callback(
    Output('location-dropdown', 'options'),
    Output('location-dropdown', 'value'),
    Input('location-search', 'value'),
    State('location-dropdown', 'value')
)
def update_location_options(search_term, selected_locations):
    if search_term:
        result = geocode_location(search_term)

        if result is not None:
            latitude, longitude = result
            new_options = [{'label': search_term, 'value': f"{latitude}, {longitude}"}]
            return new_options, [new_options[0]['value']]
        else:
            return dash.no_update, selected_locations

    return dash.no_update, selected_locations


#fig = px.line(filtered_df, x='Date', y='Peak Temp (ºC)', color='Location', title='Historical Temperature Comparison')
    #return fig







if __name__ == '__main__':
    app.run_server(debug=True)
