import os

import pandas as pd


def load_data(data_dir, news_only=False):
    tweet_df = pd.read_json(
        os.path.join(data_dir, 'tweets_classified.json'),
        orient='split')
    news_df = pd.read_json(
        os.path.join(data_dir, 'news_classified.json'),
        orient='split')
    if news_only:
        return news_df
    return tweet_df, news_df
