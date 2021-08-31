import os
from sqlalchemy import create_engine
import pandas as pd


def load_data(data_dir, news_only=False):
    "load news and tweet from jsons"
    tweet_df = pd.read_json(
        os.path.join(data_dir, 'tweets_classified.json'),
        orient='split')
    news_df = pd.read_json(
        os.path.join(data_dir, 'news_classified.json'),
        orient='split')
    if news_only:
        return news_df
    return tweet_df, news_df


def store_to_db():
    "load data and store into local sqlite db"
    engine = create_engine("sqlite:///app_db.sqlite")
    tweet_frame, news_frame = load_data("../Analysis")

    news_frame.to_sql("news_table", engine)
    tweet_frame.to_sql("tweet_table", engine)


if __name__ == "__main__":
    store_to_db()
