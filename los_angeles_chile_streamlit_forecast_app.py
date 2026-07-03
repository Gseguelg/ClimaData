import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Streamlit page setup
st.set_page_config(
    page_title="Los Ángeles, Chile | 14-Day Hourly Forecast",
    page_icon="🌦️",
    layout="wide",
)

st.title("🌦️ Hourly Forecast for Los Ángeles, Chile")
st.caption("14-day hourly forecast with interactive charts for rain probability, rain amount, wind, and temperature.")

# Fixed location: Los Ángeles, Biobío Region, Chile
LOCATION = {
    "name": "Los Ángeles, Chile",
    "latitude": -37.4697,
    "longitude": -72.3537,
    "timezone": "America/Santiago",
}

API_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_VARS = [
    "temperature_2m",
    "precipitation_probability",
    "precipitation",
    "windspeed_10m",
    "windgusts_10m",
]


@st.cache_data(ttl=30 * 60)
def fetch_forecast(latitude: float, longitude: float, timezone: str) -> pd.DataFrame:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(HOURLY_VARS),
        "forecast_days": 14,
        "timezone": timezone,
    }
    response = requests.get(API_URL, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    if "hourly" not in data:
        raise ValueError("Unexpected API response: missing 'hourly' key.")

    hourly = data["hourly"]
    df = pd.DataFrame(hourly)
    if "time" not in df.columns:
        raise ValueError("Unexpected API response: missing 'time' column.")

    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)
    return df


try:
    df = fetch_forecast(LOCATION["latitude"], LOCATION["longitude"], LOCATION["timezone"])
except Exception as exc:
    st.error(f"Could not load forecast data: {exc}")
    st.stop()

# Header metrics
now = df.iloc[0]
next_24h = df.iloc[:24]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Temperature now", f"{now['temperature_2m']:.1f} °C")
col2.metric("Rain probability now", f"{now['precipitation_probability']:.0f}%")
col3.metric("Wind avg now", f"{now['windspeed_10m']:.1f} km/h")
col4.metric("Wind gust now", f"{now['windgusts_10m']:.1f} km/h")

summary1, summary2, summary3 = st.columns(3)
summary1.metric("Max rain probability next 24h", f"{next_24h['precipitation_probability'].max():.0f}%")
summary2.metric("Total rain next 24h", f"{next_24h['precipitation'].sum():.1f} mm")
summary3.metric("Max temperature next 24h", f"{next_24h['temperature_2m'].max():.1f} °C")

st.divider()

# Interactive charts
st.subheader("Interactive forecast charts")

tab_temp, tab_rain, tab_wind = st.tabs(["Temperature", "Rain", "Wind"])

with tab_temp:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["temperature_2m"],
            mode="lines",
            name="Temperature (°C)",
            hovertemplate="%{x}<br>Temperature: %{y:.1f} °C<extra></extra>",
        )
    )
    fig.update_layout(
        title="Hourly temperature for the next 14 days",
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        hovermode="x unified",
        height=500,
        xaxis=dict(rangeslider=dict(visible=True)),
        margin=dict(l=40, r=30, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_rain:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["precipitation_probability"],
            mode="lines",
            name="Rain probability (%)",
            hovertemplate="%{x}<br>Probability: %{y:.0f}%<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            x=df["time"],
            y=df["precipitation"],
            name="Rain quantity (mm)",
            opacity=0.5,
            hovertemplate="%{x}<br>Rain: %{y:.2f} mm<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.update_layout(
        title="Rain probability and quantity",
        hovermode="x unified",
        height=500,
        xaxis=dict(rangeslider=dict(visible=True)),
        margin=dict(l=40, r=30, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_yaxes(title_text="Probability (%)", secondary_y=False)
    fig.update_yaxes(title_text="Precipitation (mm)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

with tab_wind:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["windspeed_10m"],
            mode="lines",
            name="Wind average (km/h)",
            hovertemplate="%{x}<br>Avg wind: %{y:.1f} km/h<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["windgusts_10m"],
            mode="lines",
            name="Wind max / gusts (km/h)",
            hovertemplate="%{x}<br>Max wind: %{y:.1f} km/h<extra></extra>",
        )
    )
    fig.update_layout(
        title="Wind average and maximum velocity",
        xaxis_title="Time",
        yaxis_title="Wind speed (km/h)",
        hovermode="x unified",
        height=500,
        xaxis=dict(rangeslider=dict(visible=True)),
        margin=dict(l=40, r=30, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Forecast table")
show_cols = [
    "time",
    "temperature_2m",
    "precipitation_probability",
    "precipitation",
    "windspeed_10m",
    "windgusts_10m",
]
pretty_df = df[show_cols].copy()
pretty_df.columns = [
    "Time",
    "Temperature (°C)",
    "Rain probability (%)",
    "Rain quantity (mm)",
    "Wind average (km/h)",
    "Wind max / gusts (km/h)",
]
pretty_df["Time"] = pretty_df["Time"].dt.strftime("%Y-%m-%d %H:%M")
st.dataframe(pretty_df, use_container_width=True, height=420)

st.caption(
    "Data source: Open-Meteo hourly forecast. Location fixed to Los Ángeles, Chile (Biobío Region)."
)
