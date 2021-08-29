import random


import dash
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

import dash_bootstrap_components as dbc


from webapp.layout import create_layout, fig_placeholder
from utils.load_data import load_data
from utils.text_processing import load_transformers, get_keywords
from tickers.get_tickers import get_ticker, load_api_keys, convert_to_frame


def generate_table(dataframe, max_rows=26):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +
        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


def _get_dropdown_options(frame):
    company_names = sorted(frame.matched_company.unique())
    return [
        {"label": c_name, "value": c_name} for c_name in company_names
    ]


api_keys = load_api_keys("tickers/api_keys.json")


news_df = load_data("../Analysis", news_only=True)
s_p_500_list = news_df.matched_company.unique()

tfidf_vectorizer, count_vectorizer = load_transformers(
    "../Model", mode="all")

app = dash.Dash(external_stylesheets=[dbc.themes.DARKLY])

app.layout = create_layout(
    dropdown_options=_get_dropdown_options(news_df)
    )


@app.callback(
    Output('keyword_display', 'figure'),
    Output('count_display', 'figure'),
    Input('demo-dropdown', 'value'))
def update_keywords(selected_company):

    if selected_company == "":
        return fig_placeholder, fig_placeholder

    filtered_df = news_df.query(f"matched_company == '{selected_company}'")
    keyword_df = get_keywords(
        filtered_df,
        s_p_500_list, count_vectorizer)

    count_df = filtered_df.groupby(
        [pd.Grouper(key='date', freq='W-MON')]
    ).size()

    count_df.columns = ["Number of matched news articles"]

    fig = px.bar(
        keyword_df.sort_values(by="count"),
        y="feature",
        x="count",
        hover_name="feature",
        color="count",
        template="plotly_dark",
        title="Most often occuring keywords"
    )
    fig.update_layout(transition_duration=500)

    fig2 = px.bar(
        count_df,
        template="plotly_dark",
        title="Number of matched news articles"
    )
    fig2.update_layout(transition_duration=500)

    return fig, fig2


@app.callback(
    Output('graph-1', 'figure'),
    Input('demo-dropdown', 'value'))
def update_figure(selected_company):

    if selected_company == "":
        return fig_placeholder

    filtered_df = news_df[news_df.matched_company == selected_company]

    gics_sector = filtered_df.iloc[0].gics_sector
    sector_df = news_df[news_df.gics_sector == gics_sector]

    plot_df = filtered_df.groupby(
        [pd.Grouper(key='date', freq='W-MON')]
    ).aggregate(
        {"sentiment_news": "mean"}
    )

    plot_df_sector = sector_df.groupby(
        [pd.Grouper(key='date', freq='W-MON')]
    ).aggregate(
        {"sentiment_news": "mean"}
    )

    plot_df = plot_df.merge(
        plot_df_sector, left_index=True, right_index=True,
        suffixes=(f" for {selected_company}", f" for {gics_sector}")
        )

    first = plot_df.index.min()
    last = plot_df.index.max()

    ticker = get_ticker(
        filtered_df.iloc[0]["symbol"],
        random.choice(list(api_keys["tickers"].values()))
    )

    metadata, ticker_frame = convert_to_frame(ticker)
    plot_df = plot_df.merge(
        ticker_frame, left_index=True, right_index=True, how="outer")

    plot_df = plot_df[(plot_df.index <= last) & (plot_df.index >= first)]
    plot_df["4. close"] = plot_df["4. close"] / plot_df["4. close"].iloc[0]
    plot_df.index = plot_df.index.rename("date")
    plot_df = pd.melt(plot_df.reset_index(), id_vars="date")

    fig = px.line(
        plot_df,
        x="date",
        y="value",
        hover_name="date",
        color="variable",
        template="plotly_dark")

    fig.update_traces(connectgaps=True)
    fig.update_traces(mode='lines+markers')
    fig.update_layout(transition_duration=500)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
