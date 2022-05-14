# script for matching scraped news with company list
# use zip for iterate through multiple objects
# set_value will soon be depreciated => change it!
# matcher problems to fix: description + title col
import pandas as pd
import os
from datetime import datetime
import re
#import numpy as np

# Define local directories (relative from this file)
# dir_path = os.path.dirname(os.path.realpath(__file__))
## Debug
dir_path = os.getcwd()
data_gen_path = os.path.join(dir_path, 'Data')
news_path = os.path.join(data_gen_path,'News')

data_paths = [os.path.join(dir_path, 'Data/Twitter/'),
			  os.path.join(dir_path, 'Data/News/BI/'),
			  os.path.join(dir_path, 'Data/News/Reuters/'),
			  os.path.join(dir_path, 'Data/News/cnbc/'),
			  os.path.join(dir_path, 'Data/s_p_500/'),
			  os.path.join(dir_path, 'Data/Companies/')
			  ]
# load company data
company_df = pd.read_excel(os.path.join(data_paths[5], 's_p_500_list_final.xlsx'), sheet_name=0)
company_df = company_df.fillna('')
s_p_500_list = list(set(company_df['news_name'].tolist()))
company_df.rename(columns={'news_name': 'matched_company'}, inplace=True)
company_df = company_df.drop_duplicates(subset='matched_company', keep="first")
# string to date converter
def timestamp_converter(str_timestamp, scrape_date, news_type):
	# date format conversion from:
	# https: // docs.python.org / 2 / library / datetime.html
	if news_type == 'cnbc':
		if str_timestamp.endswith('Ago'):
			date = datetime.strptime(scrape_date, '%Y-%m-%d').date()
		else:
			date = str_timestamp.split(', ', 1)[1]
			date = re.sub('Sept', 'Sep', date)
			date = datetime.strptime(date, '%d %b %Y').date()
	elif news_type == 'BI':
		date = str_timestamp.split(',', 1)[0] + ' 2018'
		date = re.sub('\\n', '', date)
		date = datetime.strptime(date, '%b. %d %Y').date()
	elif news_type == 'reuters':
		date = re.sub('/str/', '', str_timestamp)
		if date.endswith('EST'):
			date = datetime.strptime(scrape_date, '%Y-%m-%d').date()
		else:
			date = datetime.strptime(date, '%b %d %Y').date()
	return(date)

def company_matcher(dataframe, company_list, title_col, description_col = None):
	"""search for substring provided by list of strings in title or in description column of a dataframe,
	Returns new string column with matched substrings as values"""
	dataframe['matched_company'] = None
	matched_companies = []
	# loop over df

	for index, row in dataframe.iterrows():
		for company in company_list:
			# regex inspired from:
			# https://superuser.com/questions/903168/how-should-i-write-a-regex-to-match-a-specific-word
			company_regex = "(?:^|\W)(" + company + ")(?:$|\W)"
			if re.search(company_regex, row[title_col], re.IGNORECASE):
				dataframe.set_value(index, "matched_company", company)
			if description_col:
				if re.search(company_regex, row[description_col], re.IGNORECASE):
					dataframe.set_value(index, "matched_company", company)
	return(dataframe)

# load news articles and match company list to it
news_list = []
non_matched = []
count = 0
for path in data_paths[1:4]:

	# format timestamp to same date format, match all news articles with companies mentioned
	news_list.append(pd.read_json(os.path.join(path, 'scraped_articles.json'), orient='split'))
	news_list[count]['date'] = None
	print("input " + str(news_list[count].shape))
	# date column is always different, and news matching is sometimes done on different cols
	if count == 0:
		news_list[count] = company_matcher(news_list[count], s_p_500_list, 'title')
		for index, row in news_list[count].iterrows():
			row['date'] = (timestamp_converter(row['timestamp'], row['scrape_date'], 'BI'))
	elif count == 1:
		news_list[count] = company_matcher(news_list[count],s_p_500_list, 'title', 'description')
		for index, row in news_list[1].iterrows():
			row['date'] = (timestamp_converter(row['timestamp'], row['scrape_date'], 'reuters'))
	else:
		news_list[count] = company_matcher(news_list[count], s_p_500_list, 'title', 'description')
		for index, row in news_list[2].iterrows():
			row['date'] = (timestamp_converter(row['timestamp'], row['scrape_date'], 'cnbc'))
	# more cleaning
	news_list[count] = news_list[count].drop(columns=["timestamp"])

	# keep non matched articles
	non_matched.append(news_list[count][news_list[count].matched_company.isnull()])
	print("notmatched " + str(non_matched[count].shape))
	# merge matched articles with company information dataframe
	news_list[count] = pd.merge(news_list[count], company_df, how='inner', on='matched_company')
	print("matched " + str(news_list[count].shape))
	count += 1

# append matched articles and write to json
news_df = pd.concat(news_list, ignore_index=True)
news_df['description'] = news_df['description'].fillna('')
news_df.to_json(os.path.join(news_path, 'matched_articles_all.json'), orient='split')

# append non matched articles, take random sample
non_matched_df = pd.concat(non_matched, ignore_index=True)
non_matched_df = non_matched_df.sample(n = 1000, random_state= 34985798)

# delete description column for label data -> only title is available for all newspapers
non_matched_df = non_matched_df.drop(columns="description")
non_matched_df['title'] = non_matched_df['title'].str.lstrip()
# write to xlsx (human readable -> labelling for training data)
non_matched_df.to_excel(os.path.join(news_path, 'non_matched_articles_training.xlsx'))