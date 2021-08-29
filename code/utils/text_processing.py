import re
import string
import os
import csv

import numpy as np
import pandas as pd
from nltk.tokenize import TweetTokenizer
from nltk.corpus import wordnet
from nltk import PorterStemmer

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer


def remove_repeated_characters(tokens):
    # From: Text Analytics with Python A Practical Real-World Approach to
    repeat_pattern = re.compile(r'(\w*)(\w)\2(\w*)')
    match_substitution = r'\1\2\3'

    def _replace(old_word):
        if wordnet.synsets(old_word):
            return old_word
        new_word = repeat_pattern.sub(match_substitution, old_word)
        return _replace(new_word) if new_word != old_word else new_word

    correct_tokens = [_replace(word) for word in tokens]
    return correct_tokens


def load_stopwords(data_dir):
    # nltk Liste aber bereiningt (not,very usw.)
    with open(os.path.join(data_dir, "stopwords/stopwords_final.csv")) as f:
        reader = csv.reader(f, delimiter=";")
        raw = [r for r in reader]
        [stopwords] = raw
    return stopwords


def load_extended_chars(data_dir):
    # additional characters to be removed
    with open(
        os.path.join(data_dir, "stopwords/extended_characters_words.csv")
    ) as f:
        reader = csv.reader(f, delimiter=";")
        raw = [r for r in reader]
        [extended] = raw
    return extended


EXTENDED = load_stopwords("../data")
STOPWORDS = load_extended_chars("../data")


def process_text(
    tweet,
    remove_url=True,
    strip_handles=True,
    remove_stopword=True,
    remove_punctation=True,
    stemming=True,
    remove_characters=True,
    remove_extended_words=True
):
    """
    Function to process tweets or other texts. Input is string and output is
    tokens text gets stemmed, puncuations and stopwords removed
    """
    processedtext = tweet
    tokenizer = TweetTokenizer(
        strip_handles=strip_handles, reduce_len=False, preserve_case=False
    )  # perserve_case and reduce_len must be False

    if remove_url:
        # http://www.noah.org/wiki/RegEx_Python
        processedtext = re.sub(
            (r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]'
                r'|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            '',
            processedtext
        )
        processedtext = re.sub(
            (r'www.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]'
                r'|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            '',
            processedtext
        )
        processedtext = re.sub(
            r'[a-zA-Z0-9+_\-\.]+@[0-9a-zA-Z][.-0-9a-zA-Z]*.[a-zA-Z]+',
            "",
            processedtext
        )

    if remove_punctation is True:
        processedtext = processedtext.translate(
            str.maketrans("", "", string.punctuation)
        )

    tokens = tokenizer.tokenize(processedtext)

    if remove_extended_words is True:
        tokens = [w for w in tokens if w not in EXTENDED]

    if remove_stopword is True:
        tokens = [w for w in tokens if w not in STOPWORDS]

    if stemming is True:
        stemmer = PorterStemmer()
        tokens = [stemmer.stem(s) for s in tokens]

    if remove_characters is True:
        tokens = remove_repeated_characters(tokens)

    return tokens


def load_transformers(model_path, mode="all"):
    # vocab = load(
    #    os.path.join(
    #        model_path,
    #        'vocab_train ' + mode + '_mono_bi_gram.joblib'
    #    )
    # )

    tfidf_vectorizer = TfidfVectorizer(
        tokenizer=process_text,
        ngram_range=(1, 2),
        use_idf=True,
        smooth_idf=True,
        # vocabulary=vocab
    )

    countvectorizer_qual = CountVectorizer(
        tokenizer=process_text,
        ngram_range=(2, 2),
        # vocabulary=vocab
    )

    return tfidf_vectorizer, countvectorizer_qual


def top_counts(dtm, row_index, vocab, top_n=25):
    """ Get top n count values in row from sparse dtm and return
    them with their corresponding feature names."""
    row = np.squeeze(dtm[row_index].toarray())
    topn_ids = np.argsort(row)[::-1][:top_n]

    def inverseGet(input_dict, value_find):
        # lookup features from vocab
        for key, value in input_dict.items():
            if value == value_find:
                return key

    top_feats = [(inverseGet(vocab, i), row[i]) for i in topn_ids]
    df = pd.DataFrame(top_feats)
    df.columns = ['feature', 'count']
    return df


def get_keywords(frame, s_p_500_list, count_vectorizer):
    news_text = frame['title'].str.cat(sep=' ')
    news_text = re.sub(
        "|".join(s_p_500_list), "",
        news_text.lower(), flags=re.IGNORECASE)

    qualitativ = count_vectorizer.fit_transform([news_text])
    return top_counts(qualitativ, 0, count_vectorizer.vocabulary_, top_n=15)
