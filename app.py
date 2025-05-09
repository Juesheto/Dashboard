# -*- coding: utf-8 -*-
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import os

# Cargar datos
spotify_df = pd.read_csv("Popular_Spotify_Songs.csv", encoding="latin1")

# Preprocesamiento de fechas
for col in ['released_year', 'released_month', 'released_day']:
    spotify_df[col] = pd.to_numeric(spotify_df[col], errors='coerce')
spotify_df = spotify_df.dropna(subset=['released_year', 'released_month', 'released_day'])
spotify_df[['released_year', 'released_month', 'released_day']] = spotify_df[['released_year', 'released_month', 'released_day']].astype(int)
spotify_df['release_date'] = pd.to_datetime(dict(
    year=spotify_df['released_year'],
    month=spotify_df['released_month'],
    day=spotify_df['released_day']
), errors='coerce')
spotify_df = spotify_df.dropna(subset=['release_date'])
spotify_df['streams'] = pd.to_numeric(spotify_df['streams'], errors='coerce')

# App
app = Dash(__name__)
server = app.server
app.title = "Spotify Popular Songs Dashboard"

# Layout
app.layout = html.Div([
    html.H1("🎵 Spotify Popular Songs (2010–2023)", style={'textAlign': 'center'}),

    html.Div([
        html.P("Este tablero interactivo permite explorar tendencias de canciones populares de Spotify entre 2010 y 2023."),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    html.Div([
        html.Label("Rango de fechas:"),
        dcc.DatePickerRange(
            id='date_range',
            min_date_allowed=spotify_df['release_date'].min(),
            max_date_allowed=spotify_df['release_date'].max(),
            start_date=spotify_df['release_date'].min(),
            end_date=spotify_df['release_date'].max(),
            display_format='YYYY-MM-DD'
        )
    ], style={'marginBottom': '30px', 'textAlign': 'center'}),

    html.Div([
        html.Div([
            html.H3("Evolución de Streams por Fecha"),
            dcc.Graph(id='line_graph'),
            html.Div([
                html.Label("Color de fondo:"),
                dcc.RadioItems(
                    id='line_color_selector',
                    options=[
                        {'label': 'Claro', 'value': 'white'},
                        {'label': 'Oscuro', 'value': 'black'}
                    ],
                    value='white',
                    labelStyle={'display': 'inline-block', 'marginRight': '10px'}
                )
            ], style={'textAlign': 'center'})
        ], style={
            'width': '48%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '10px',
            'boxShadow': '0 0 10px rgba(0,0,0,0.1)',
            'borderRadius': '10px'
        }),

        html.Div([
            html.H3("Top 5 Canciones Más Escuchadas por Año"),
            dcc.Dropdown(
                id='year_dropdown_songs',
                options=[{'label': str(y), 'value': y} for y in sorted(spotify_df['released_year'].dropna().unique())],
                value=2020
            ),
            dcc.Graph(id='top_songs_chart')
        ], style={
            'width': '48%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '10px',
            'boxShadow': '0 0 10px rgba(0,0,0,0.1)',
            'borderRadius': '10px'
        })
    ], style={'textAlign': 'center'}),

    html.Div([
        html.Div([
            html.H3("Top 10 Artistas por Año"),
            dcc.Dropdown(
                id='year_dropdown',
                options=[{'label': str(y), 'value': y} for y in sorted(spotify_df['released_year'].dropna().unique())],
                value=2020
            ),
            dcc.Graph(id='top_artists_chart')
        ], style={
            'width': '48%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '10px',
            'boxShadow': '0 0 10px rgba(0,0,0,0.1)',
            'borderRadius': '10px'
        }),

        html.Div([
            html.H3("Distribución del Modo Musical por Año"),
            dcc.Dropdown(
                id='year_dropdown_pie',
                options=[{'label': str(y), 'value': y} for y in sorted(spotify_df['released_year'].dropna().unique())],
                value=2020
            ),
            dcc.Graph(id='pie_chart')
        ], style={
            'width': '48%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '10px',
            'boxShadow': '0 0 10px rgba(0,0,0,0.1)',
            'borderRadius': '10px'
        })
    ], style={'textAlign': 'center'})
])

# Callbacks
@app.callback(
    Output('line_graph', 'figure'),
    Input('date_range', 'start_date'),
    Input('date_range', 'end_date'),
    Input('line_color_selector', 'value')
)
def update_line(start, end, color):
    filtered = spotify_df[(spotify_df['release_date'] >= start) & (spotify_df['release_date'] <= end)]
    if filtered.empty:
        fig = go.Figure()
        fig.add_annotation(text="No hay datos en este rango.",
                           x=0.5, y=0.5, showarrow=False, font=dict(size=18))
        return fig

    trend = filtered.groupby('release_date')['streams'].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend['release_date'], y=trend['streams'], mode='lines', name='Streams'))
    fig.update_layout(
        title='Evolución de Streams',
        plot_bgcolor=color,
        paper_bgcolor=color,
        xaxis=dict(rangeslider=dict(visible=True), type='date')
    )
    return fig

@app.callback(
    Output('top_artists_chart', 'figure'),
    Input('year_dropdown', 'value')
)
def update_top_artists(selected_year):
    filtered = spotify_df[spotify_df['released_year'] == selected_year].copy()
    if filtered.empty:
        fig = go.Figure()
        fig.add_annotation(text="No hay datos para este año.",
                           x=0.5, y=0.5, showarrow=False)
        return fig

    top_artists = (
        filtered.groupby('artist(s)_name')['streams']
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    fig = px.bar(top_artists, x='artist(s)_name', y='streams',
                 title=f"Top 10 Artistas Más Escuchados en {selected_year}",
                 labels={'artist(s)_name': 'Artista', 'streams': 'Streams'})
    fig.update_layout(xaxis_tickangle=-45, height=500)
    return fig

@app.callback(
    Output('pie_chart', 'figure'),
    Input('year_dropdown_pie', 'value')
)
def update_pie(selected_year):
    filtered = spotify_df[spotify_df['released_year'] == selected_year].copy()
    if filtered.empty or 'mode' not in filtered.columns:
        fig = go.Figure()
        fig.add_annotation(text="No hay datos válidos para 'mode'.",
                           x=0.5, y=0.5, showarrow=False)
        return fig

    filtered['mode'] = filtered['mode'].map({'Major': 'Mayor (Alegre)', 'Minor': 'Menor (Triste)'})
    counts = filtered['mode'].value_counts().reset_index()
    counts.columns = ['Modo', 'Cantidad']
    if counts.empty:
        fig = go.Figure()
        fig.add_annotation(text="No hay datos para mostrar.",
                           x=0.5, y=0.5, showarrow=False)
        return fig

    fig = px.pie(counts, names='Modo', values='Cantidad',
                 title=f"Distribución del Modo Musical en {selected_year}")
    return fig

@app.callback(
    Output('top_songs_chart', 'figure'),
    Input('year_dropdown_songs', 'value')
)
def update_top_songs(selected_year):
    filtered = spotify_df[spotify_df['released_year'] == selected_year].copy()
    if filtered.empty:
        fig = go.Figure()
        fig.add_annotation(text="No hay datos para este año.",
                           x=0.5, y=0.5, showarrow=False)
        return fig

    top_songs = (
        filtered.groupby('track_name')['streams']
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )

    fig = px.bar(top_songs, x='track_name', y='streams',
                 title=f"Top 5 Canciones Más Escuchadas en {selected_year}",
                 labels={'track_name': 'Canción', 'streams': 'Streams'})
    fig.update_layout(xaxis_tickangle=-45, height=500)
    return fig

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
