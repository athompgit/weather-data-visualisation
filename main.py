from dash import dcc, callback_context, html, Input, Output, State, Dash, dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import requests_cache
from retry_requests import retry
import openmeteo_requests
from datetime import datetime, timedelta, date, time, timezone
import duckdb
import dash_bootstrap_components as dbc




# 1) Cache for historical data (never expires)
cache_session_hist = requests_cache.CachedSession('historical_cache', expire_after=-1)
retry_session_hist = retry(cache_session_hist, retries=5, backoff_factor=0.2)
openmeteo_hist = openmeteo_requests.Client(session=retry_session_hist)

# 2) Cache for current weather data (expires after 1 hour)
cache_session_current = requests_cache.CachedSession('current_cache', expire_after=3600)
retry_session_current = retry(cache_session_current, retries=5, backoff_factor=0.2)
openmeteo_current = openmeteo_requests.Client(session=retry_session_current)


def get_current_temperature(lat, lon):
    db_path = ("weather_data.duckdb")
    with duckdb.connect(db_path) as conn:

        cached_temp = conn.execute(
            "SELECT temperature FROM weather_cache WHERE latitude = ? AND longitude = ? AND timestamp >= ? ORDER BY timestamp DESC LIMIT 1",
            [lat, lon, datetime.now(timezone.utc) - timedelta(hours=1)]
        ).fetchone()

        if cached_temp:
            return {"temperature": cached_temp[0]}

        # If no cached data, fetch from API
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "forecast_days": 1,
            "current_weather": True
        }
        responses = openmeteo_current.weather_api(url, params=params)
        response = responses[0]
        current_temperature_2m = response.Current().Variables(0).Value()


        conn.execute(
            "INSERT INTO weather_cache (latitude, longitude, temperature, timestamp) VALUES (?, ?, ?, ?)",
            [lat, lon, current_temperature_2m, datetime.now(timezone.utc)]
        )
        conn.commit()

        return {"temperature": current_temperature_2m}




timezone_offset = None


def get_current_time(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "auto",
        "current_weather": True
    }

    try:
        responses = openmeteo_current.weather_api(url, params=params)
        response = responses[0]


        timezone_offset_seconds = response.UtcOffsetSeconds()


        local_time = datetime.now(timezone.utc) + timedelta(seconds=timezone_offset_seconds)

        return {"time": local_time.strftime("%H:%M")}

    except Exception as e:
        print(f"Error fetching time data: {e}")
        return {"time": "N/A"}


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
        responses = openmeteo_hist.weather_api(url, params=params)
        print("API responses:", responses)

        if not responses or len(responses) == 0:
            print("mo response returned from api for these parameters")
            return pd.DataFrame()
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
        return []

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={search_term}&count=5"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data and 'results' in data:
            results = []
            for result in data['results']:
                if 'latitude' in result and 'longitude' in result and 'admin1' in result and 'country':
                    latitude = result['latitude']
                    longitude = result['longitude']
                    name = result['name']
                    admin1 = result.get('admin1', '')
                    country = result['country']
                    formatted_name = f"{name}, {admin1}, {country}" if admin1 else f"{name}, {country}"
                    results.append({'label': formatted_name, 'value': f"{latitude}, {longitude}"})
            return results
        else:
            print(f"No results for '{search_term}'.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Geocoding Error: {e}")
        return []
    except (KeyError, TypeError) as e:
        print(f"Error parsing geocoding data: {e}")
        return []



external_stylesheets = ['/Users/audrey/PycharmProjects/weather-data-visualisation/assets/style.css', dbc.themes.BOOTSTRAP]

# Dash App Setup
app = Dash(__name__, external_stylesheets=external_stylesheets)

initial_dropdown_options = []

today = date.today()
min_date = today - timedelta(days=31000)

# app.layout defines content and structure of app's UI
app.layout = html.Div(className='container', children=[
    html.H1("Weather Data Visualisation"),

    dbc.Row([
        dbc.Col(dbc.Button("Current Temperature/Time", id='current-data-button', style={'height': '50px', 'margin': '10px'}), width=6),
        dbc.Col(dbc.Button("Historical Data", id="historical-data-button", style={'height': '50px', 'margin': '10px'}), width=6),
    ]),

    html.Div(id='content-area', children=[
        html.P("Please select a data type")
    ]),

    html.Div(id="current-data-content", style={'display': 'none'}, children=[
        html.Div(className='search-container', children=[
            dcc.Input(id='location-search', placeholder='Enter a location', type='text', className='search-input'),
            dcc.Dropdown(
                id='location-dropdown-current',
                placeholder="Select a location",
            ),
        ]),
        html.Div(className='widget-container', children=[
            html.Div(id='current-temp-display', className='current-temp-widget'),
            html.Div(id='current-time-display', className='current-time-widget'),
        ]),
    ]),
    html.Div(id='historical-data-content', style={'display': 'none'}, children=[
        html.Div(className='search-container', children=[
            dcc.Input(id='location-search-graph', placeholder='Enter location(s)', type='text', className='search-input'),
            dcc.Dropdown(
                id='location-dropdown-graph',
                placeholder="Select location(s)",
                multi=True
            ),
        ]),
        dcc.Graph(id='weather-graph', className='graph'),
        dcc.DatePickerRange(
            id='date-range-picker',
            min_date_allowed=min_date,
            max_date_allowed=today,
            start_date=min_date,
            end_date=today
        ),
    ])
])


@app.callback(
    [Output('current-temp-display', 'children'),
     Output('current-time-display', 'children')],
    [Input('location-dropdown-current', 'value')]
)
def update_temp_and_time(selected_location):
    if not selected_location:
        return html.Div("No location selected.", className='error'), html.Div("No location selected.", className='error')

    try:
        lat, lon = map(float, selected_location.split(','))
    except ValueError:
        return html.Div("Invalid location format.", className='error'), html.Div("Invalid location format.", className='error')

    # Fetch updated temperature and time
    current_temp = get_current_temperature(lat, lon)
    rounded_temp = round(current_temp['temperature'])

    current_time = get_current_time(lat, lon)

    temp_div = html.Div([
        html.H2(f"{rounded_temp}ºC", className='temp-number'),
        html.P("Current Temperature", className='temp-label')
    ], className="current-temp-widget")

    time_div = html.Div([
        html.H2(f"{current_time['time']}", className='time-number'),
        html.P("Local Time", className='time-label')
    ], className="current-time-widget")

    return temp_div, time_div



# Callback for temp and time display
@app.callback(
    Output('location-dropdown-current', 'options'),
    Output('location-dropdown-current', 'value'),
    Input('location-search', 'value'),
    State('location-dropdown-current', 'value')
)
def update_location_options(search_term, selected_locations):
    if search_term:
        results = geocode_location(search_term)
        if results:
            return results, [results[0]['value']]
        else:
            return [], []
    else:
        return [], []

    #return dash.no_update, selected_locations

@app.callback(
    Output('location-dropdown-graph', 'options'),
    Output('location-dropdown-graph', 'value'),
    Input('location-search-graph', 'value'),
    State('location-dropdown-graph', 'value')
)
def update_location_options_graph(search_term, selected_locations):
    if search_term:
        results = geocode_location(search_term)
        if results:
            return results, [results[0]['value']]
        else:
            return [],[]
    else:
        return [],[]


# Callback for weather graph, l
@app.callback(
    Output('weather-graph', 'figure'),
    Input('location-dropdown-graph', 'value'),
    Input('date-range-picker', 'start_date'),
    Input('date-range-picker', 'end_date')
)
def update_graph(selected_locations, start_date, end_date):

    if not selected_locations:
        return dash.no_update

    fig = go.Figure()
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

    if not isinstance(selected_locations, list):
        selected_locations = [selected_locations]

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

@app.callback(
    Output("current-data-content", "style"),
    Output('historical-data-content', 'style'),
    Input('current-data-button', 'n_clicks'),
    Input("historical-data-button", 'n_clicks'),
    State("current-data-content", 'style'),
    State('historical-data-content', 'style')
)
def toggle_content(current_clicks, historical_clicks, current_style, historical_style):
    ctx = callback_context
    if not ctx.triggered:
        return {'display': 'none'}, {'display': 'none'}
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'current-data-button':
            if current_style['display'] == 'none':
                return {'display': 'block'}, {'display': 'none'}
            else:
                return {'display': 'none'}, {'display': 'none'}
        elif button_id == 'historical-data-button':
            if historical_style['display'] == 'none':
                return {'display': 'none'}, {'display': 'block'}
            else:
                return {'display': 'none'}, {'display': 'none'}


if __name__ == '__main__':
    app.run(debug=True)