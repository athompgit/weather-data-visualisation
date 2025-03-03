from dash import dcc, html, Input, Output, State, Dash, dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import requests_cache
from retrying import retry
import openmeteo_requests
from datetime import datetime, timedelta, date


cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


def get_weather_data(lat, lon, start_date, end_date):

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "hourly": "temperature_2m",
        "wind_speed_unit": "mph"
    }
    try:
        responses = openmeteo.weather_api(url, params=params)
        print("API responses:", responses)

        if not responses or len(responses) == 0:
            print("mo response returned from api for these parameters")
            return pd.DataFrame
        response = responses[0]


        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            ),
            "temperature_2m": hourly_temperature_2m
        }
        hourly_dataframe = pd.DataFrame(data=hourly_data)

        hourly_dataframe["date"] = pd.to_datetime(hourly_dataframe["date"]).dt.tz_convert(None)
        return hourly_dataframe

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return pd.DataFrame()


def create_weather_graph(meteo_df, title):

    if meteo_df.empty:
        return go.Figure(data=[go.Scatter()],
                         layout=go.Layout(title=title, xaxis=dict(title='Time'), yaxis=dict(title='Temperature')))

    fig = px.line(meteo_df, x='date', y='temperature_2m', title=title)
    return fig


def geocode_location(search_term):

    if not search_term:
        return None

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
            return None
    except requests.exceptions.RequestException as e:
        print(f"Geocoding Error: {e}")
        return None
    except (KeyError, TypeError) as e:
        print(f"Error parsing geocoding data: {e}")
        return None



#Dash App Setup
external_stylesheets = ['style.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)

initial_dropdown_options = []

today = date.today()
min_date = today - timedelta(days=31000)

#Defines content and structure of app's UI
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
])



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
            new_option = {'label': search_term, 'value': f"{latitude},{longitude}"}
            return [new_option], [new_option['value']]
        else:
            # No valid result: do not update
            return dash.no_update, selected_locations
    return dash.no_update, selected_locations


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
            for trace in temp_fig.data:

                trace.name = location
                fig.add_trace(trace)
        else:
            print(f"No available data for {location}")


    fig.update_layout(
        title="Historical Weather Comparison",
        xaxis_title="Time",
        yaxis_title="Temperature (ºC)"
    )
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
