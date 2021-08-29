import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc


def create_layout(**kwargs):

    dropdown_options = kwargs["dropdown_options"]

    layout = html.Div(children=[
        html.H1(children='Enigma'),

        html.Div(children='''
            Decoding industry sentiment
        '''),
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
                        dcc.Graph(id='graph-1')
                    ]
                )
            )
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="keyword_display")),
                dbc.Col(dcc.Graph(id="count_display")),
            ]
        )
    ])

    return layout


fig_placeholder = {
    "layout": {
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
