
# theory to sgd
# https://scikit-learn.org/stable/modules/sgd.html
# citing: https://scikit-learn.org/stable/about.html#citing-scikit-learn
# https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn import metrics
from joblib import dump
import csv
import numpy as np


from utils import text_processing

dir_path = os.getcwd()
train_path = os.path.join(dir_path, 'Data/Training_data/training.1600000.processed.noemoticon.csv')

# retrieved list of stopwords from nltk module and changed it for our needs
# from nltk.corpus import stopwords
# print(stopwords.words("english"))
with open(os.path.join(dir_path, "Data/stopwords/stopwords_final.csv")) as f:  # nltk Liste aber bereiningt (not,very usw.)
	reader = csv.reader(f, delimiter=";")
	raw = [r for r in reader]
	[stopwords] = raw

with open(os.path.join(dir_path, "Data/stopwords/extended_characters_words.csv")) as f:  # additional characters to be removed
	reader = csv.reader(f, delimiter=";")
	raw = [r for r in reader]
	[extended] = raw


def sentiment_rescaler(number):
	"""function to rescale values to negative and positive (0-1)
	0 = negative, 4 = positive => binary classification"""
	if number == 4:
		return 1
	elif number == 0:
		return 0
	else:
		return None

# load training tweets
tweet_df = pd.read_csv(train_path,  encoding='latin-1', header= None, names= ['sentiment', 'id', 'timestamp',
																			  'query','name', 'text'])
tweet_df['sentiment_binary'] = tweet_df['sentiment'].apply(sentiment_rescaler)
tweet_df = tweet_df.drop(columns=["timestamp", "query", "name", "sentiment", "id"])

# load articles
news_df = pd.read_excel(os.path.join(dir_path, 'Data/Training_data/non_matched_articles_training_labeled.xlsx'), sheet = 0)
news_df = news_df.drop(columns=['matched_company', 'date', 'scrape_date', 'source'])
news_df = news_df.dropna()
news_df.rename(columns = {"title": "text"}, inplace=True)

# define possible training modes and features
modes = ['all','tweets_only', 'news_only']
features = [(1,1), (2,2), (1,2)]
feature_name =  ['monogram', 'bigram', 'mono_bi_gram']
f_count = 0

# Machine learning setup:
# use different kind of training data, split into test and train, do grid search and save vocabs and models
# loop over different training sets
for feature in features:
	model_metrics = []
	model_accuracy = []
	model_auc = []
	for mode in modes:
		# sample weights

		# construct training texts
		if mode == 'all':
			news_df['weight'] = 1
			tweet_df['weight'] = news_df.shape[0] / tweet_df.shape[0]
			train_list = [news_df, tweet_df]
			text_train_list = []
			text_test_list = []
			sent_train_list = []
			sent_test_list = []
			weights_train_list = []
			weights_test_list = []
			for set in train_list:
				# split overall train into train and test sample (cross validation is done within GridSearch
				# adapted from:
				# https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html
				text_train, text_test, sent_train, sent_test, weights_train, weights_test = train_test_split(
					set['text'],
					set['sentiment_binary'],
					set['weight'],
					test_size=0.10, random_state=123)
				text_train_list.append(text_train)
				text_test_list.append(text_test)
				sent_train_list.append(sent_train)
				sent_test_list.append(sent_test)
				weights_train_list.append(weights_train)
				weights_test_list.append(weights_test)
			text_train = pd.concat(text_train_list)
			text_test = pd.concat(text_test_list)
			sent_train = pd.concat(sent_train_list)
			sent_test = pd.concat(sent_test_list)
			weights_train = pd.concat(weights_train_list)
			weights_test = pd.concat(weights_test_list)

		elif mode == 'tweets_only':
			tweet_df['weight'] = 1
			train_df = tweet_df
			# split overall train into train and test sample (cross validation is done within GridSearch
			text_train, text_test, sent_train, sent_test, weights_train, weights_test = train_test_split(train_df['text'],
																									 train_df[
																										 'sentiment_binary'],
																									 train_df['weight'],
																									 test_size=0.10,
																									 random_state=123)
		else:
			news_df['weight'] = 1
			train_df = news_df
			# split overall train into train and test sample (cross validation is done within GridSearch
			text_train, text_test, sent_train, sent_test, weights_train, weights_test = train_test_split(train_df['text'],
																									 train_df[
																										 'sentiment_binary'],
																									 train_df['weight'],
																									 test_size=0.10,
																									 random_state=123)
		# custom tokenization and vectorizing
		# adpated from:
		# https://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html
		# https://scikit-learn.org/stable/modules/feature_extraction.html
		tfidf_vectorizer = TfidfVectorizer(tokenizer=text_processing, ngram_range=feature, use_idf=True, smooth_idf=True)
		tfs_train = tfidf_vectorizer.fit_transform(text_train)

		vocab = tfidf_vectorizer.vocabulary_
		dump(vocab, os.path.join(dir_path, 'Model/vocab_train ' + mode + '_' + feature_name[f_count] +'.joblib'))

		# build and fit model over grid of different model params
		# reasonable guess for max sample is 10**6 observations => set max epoches according
		# https://scikit-learn.org/stable/modules/sgd.html#stochastic-gradient-descent-for-sparse-data
		classifier = SGDClassifier(loss='log', random_state=123, penalty='elasticnet', max_iter=np.ceil(max(10,10**6/len(text_train))))

		params = {
			"alpha": (10.0**-np.arange(1,10)),
			"penalty": ('l1','l2', 'elasticnet')
		}
		# Gridsearch adapted from:
		# https://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html
		gridsearch = GridSearchCV(classifier, params, cv=5, iid=False)
		fitted_model = gridsearch.fit(tfs_train, sent_train, sample_weight = weights_train)

		dump(fitted_model, os.path.join(dir_path, 'Model/text_classifier_ '+ mode +'_'+ feature_name[f_count] +'.joblib'))

		# evaluation metrics based on test set
		tfs_test = tfidf_vectorizer.transform(text_test)
		predicted_sent = fitted_model.predict(tfs_test)
		predicted_sent_proba = fitted_model.predict_proba(tfs_test)

		model_metrics.append(metrics.classification_report(sent_test,
												  predicted_sent, sample_weight=weights_test))
		model_accuracy.append(metrics.accuracy_score(sent_test, predicted_sent))
		model_auc.append(metrics.roc_auc_score(sent_test, [prob[1] for prob in predicted_sent_proba]))
		print("finished with " + mode)
	dump(model_metrics, os.path.join(dir_path, 'Model/further_evaluation_metrics_' + feature_name[f_count] +'.joblib'))
	dump(model_accuracy, os.path.join(dir_path, 'Model/accuracy_metrics_'+ feature_name[f_count] +'.joblib'))
	dump(model_auc, os.path.join(dir_path, 'Model/auc_'+ feature_name[f_count] + '.joblib'))
	f_count += 1
