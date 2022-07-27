from dash import html
from dash import dcc
import dash_bootstrap_components as dbc


def create_layout(**kwargs):

    dropdown_options = kwargs["dropdown_options"]

    layout = html.Div(children=[
        html.H1(children='Enigma',  style={"margin": "10px"}),

        html.Div(children='''
            Decoding industry sentiment
        ''',  style={"margin": "10px"}),
        dbc.Button(
            "Show Info",
            id="open-offcanvas", n_clicks=0, style={"margin": "20px"}
        ),
        dbc.Offcanvas(
            [html.B("This app is still in early development", style={"margin-bottom": "20px"}),
            html.P(
                """
                Data has been gathered from twitter and various online news sources.
                Sentiment scores (0-1) have been calculated based on a stochasticd gradient 
                classifier (logistic modell) 
                which in turn used a TF-IDF Vectorizer as feature extractor.
                By using the dropdown menu,  one can search for a company and display 
                all infos regarding news and tweet sentiment.
                """, 
                style={"margin-bottom": "20px"}
            ),
            html.A("Github Repo", href='https://github.com/thoemi123/enigma', target="_blank")
            ],
            id="offcanvas",
            title="Decoding industry sentiment",
            is_open=False,
        ),
        dbc.Row(
            dbc.Col(
                html.Div(
                    children=[
                        dcc.Dropdown(
                            id='demo-dropdown',
                            options=dropdown_options,
                            value='',
                            style={"color": "#303030"}
                        ),
                        dcc.Graph(id='graph-1', style={"display": "none"})
                    ]
                )
            )
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="keyword_display", style={"display": "none"})),
                dbc.Col(dcc.Graph(id="count_display", style={"display": "none"})),
            ]
        )
    ])

    return layout


fig_placeholder = {
    "layout": {
        "paper_bgcolor": "#222",
        "xaxis": {
            "visible": False
        },
        "yaxis": {
            "visible": False,
            "annotations": [
                {
                    "text": "No matching data found",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {
                        "size": 28
                    }
                }
            ]
        }
    }
}
