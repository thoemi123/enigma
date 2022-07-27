import random
from typing import Tuple


import dash
from dash import html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine
import dash_bootstrap_components as dbc


from webapp.layout import create_layout, fig_placeholder
from utils.text_processing import load_transformers, get_keywords
from tickers.get_tickers import get_ticker, load_api_keys, convert_to_frame


ENGINE = create_engine("sqlite:///app_db.sqlite")


def generate_table(dataframe: pd.DataFrame, max_rows=26) -> html.Table:
    """
    Transform dataframe into html table

    Parameters
    ----------
    dataframe : pd.DataFrame

    max_rows : int, optional (default=26)

    Returns
    -------
        html table 
    """
    return html.Table(
        [html.Tr([html.Th(col) for col in dataframe.columns])] +
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


def get_sp_500_list(engine) -> pd.Series:
    """
    select avaiable list of companies in data
    """
    frame = pd.read_sql("select distinct matched_company from news_table", engine)
    return sorted(frame.matched_company.unique())


def _get_dropdown_options(engine):
    # create dropdown menu input
    company_names = get_sp_500_list(engine)
    return [
        {"label": c_name, "value": c_name} for c_name in company_names
    ]


def calc_count_frames(selected_company: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate counts of news article per companie and keywords

    Parameters
    ----------
    selected_company : str
    
    Returns:
        Two dataframes containing keywords and count numbers
    """
    news_df = pd.read_sql(
        """
        select [date], matched_company, title
        from news_table
        """,
        ENGINE
    )
    news_df.date = pd.to_datetime(news_df.date)

    filtered_df = news_df.query(f"matched_company == '{selected_company}'")
    keyword_df = get_keywords(
        filtered_df,
        get_sp_500_list(ENGINE),
        count_vectorizer)

    count_df = filtered_df.groupby(
        [pd.Grouper(key='date', freq='W-MON')]
    ).size()

    count_df.columns = ["Number of matched news articles"]

    return keyword_df, count_df


def calc_sentiment_frame(selected_company):
    news_df = pd.read_sql(
        """
        select
            [date],
            matched_company,
            sentiment_news,
            sentiment_all,
            gics_sector,
            symbol
        from news_table
        """,
        ENGINE
    )

    news_df.date = pd.to_datetime(news_df.date)
    filtered_df = news_df[news_df.matched_company == selected_company]

    gics_sector = filtered_df.iloc[0].gics_sector
    sector_df = news_df[news_df.gics_sector == gics_sector]

    tweet_df = pd.read_sql(
        f"""
        select
            date,
            sentiment_tweet
        from tweet_table where sector = '{gics_sector}'
        """, ENGINE
    )
    tweet_df.date = pd.to_datetime(tweet_df.date)

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

    tweet_df = tweet_df.groupby(
        [pd.Grouper(key='date', freq='W-MON')]
    ).aggregate(
        {"sentiment_tweet": "mean"}
    ).rename(columns={"sentiment_tweet": f"sentiment_tweet for {gics_sector}"})

    plot_df = plot_df.merge(
        plot_df_sector, left_index=True, right_index=True,
        suffixes=(f" for {selected_company}", f" for {gics_sector}")
        ).merge(
            tweet_df,  left_index=True, right_index=True,
        )
    return plot_df, filtered_df.iloc[0]["symbol"]


def add_ticker_frame(plot_df, ticker_symbol, add_ticker=False):

    first = plot_df.index.min()
    last = plot_df.index.max()

    if add_ticker:
        ticker = get_ticker(
            ticker_symbol,
            random.choice(list(api_keys["tickers"].values()))
        )

        ticker_frame = convert_to_frame(ticker)
        plot_df = plot_df.merge(
            ticker_frame, left_index=True, right_index=True, how="outer")
        plot_df["4. close"] = plot_df["4. close"] / plot_df["4. close"].iloc[0]

    plot_df = plot_df[(plot_df.index <= last) & (plot_df.index >= first)]
    
    plot_df.index = plot_df.index.rename("date")
    return pd.melt(plot_df.reset_index(), id_vars="date")


api_keys = load_api_keys("tickers/api_keys.json")


tfidf_vectorizer, count_vectorizer = load_transformers(
    "../Model", mode="all")

app = dash.Dash(external_stylesheets=[dbc.themes.DARKLY])

app.layout = create_layout(
    dropdown_options=_get_dropdown_options(ENGINE)
    )


@app.callback(
    Output('keyword_display', 'figure'),
    Output('keyword_display', 'style'),
    Output('count_display', 'figure'),
    Output('count_display', 'style'),
    Input('demo-dropdown', 'value'))
def update_keywords(selected_company: str):
    """
    Update keyword and count graph

    Parameters
    ----------
    selected_company: str
    """
    if selected_company == "":
        return fig_placeholder, {"display": "none"}, fig_placeholder, {"display": "none"}

    keyword_df, count_df = calc_count_frames(selected_company)

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

    return fig, {}, fig2, {}


@app.callback(
    Output('graph-1', 'figure'),
    Output('graph-1', 'style'),
    Input('demo-dropdown', 'value'))
def update_figure(selected_company: str):
    """
    Update plotly time series

    Parameters
    ----------
    selected_company : str
        Company name

    Returns
    -------
        plotly figure
    """
    if selected_company == "":
        return fig_placeholder, {"display": "none"}

    plot_df, ticker_symbol = calc_sentiment_frame(selected_company)
    plot_df = add_ticker_frame(plot_df, ticker_symbol)

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
    return fig, {}


@app.callback(
    Output("offcanvas", "is_open"),
    Input("open-offcanvas", "n_clicks"),
    [State("offcanvas", "is_open")],
)
def open_canvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(debug=True)
