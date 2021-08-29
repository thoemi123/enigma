import json
import requests

import pandas as pd
#  https://github.com/prediqtiv/alpha-vantage-cookbook/blob/master/symbol-lists.md


def load_api_keys(json_file):
    with open(json_file, "r") as json_f:
        keys = json.load(json_f)
    return keys


# London Stock Exchange: LON
# Xetra: DEX


def get_ticker(ticker_symbol, api_key, output_size="full"):
    url = "https://www.alphavantage.co/query"
    url_params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "outputsize": output_size,
        "symbol": ticker_symbol,
        "apikey": api_key
    }
    r = requests.get(url, params=url_params)
    return r.json()


def convert_to_frame(json_ticker, cols=["4. close"]):
    metadata = json_ticker["Meta Data"]
    time_frame = pd.DataFrame.from_dict(
        json_ticker["Time Series (Daily)"]
    ).transpose()[cols]
    for c in cols:
        time_frame[c] = time_frame[c].astype(float)
    return metadata, time_frame

