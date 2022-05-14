# to-do: add relative path and check if output folder exists/
# dir_path = os.path.dirname(os.path.realpath(__file__))
# Scrape business news pages
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime
import os

dir_path = os.getcwd()

def html_extractor(input_soup, css_snippet):
	"""extract specific html elements and store elements as text in a list"""
	elements_text = []
	elements = input_soup.select(css_snippet)
	for elem in elements:
		elements_text.append(elem.get_text())
	return(elements_text)

# set parameters and url for reuters
scrape_params = {
	'view': 'page',
	'page': '',
	'pageSize': '10'
}
url = 'https://www.reuters.com/news/archive/businessnews'

# define lists for storing data
reuters_titles = []
reuters_descriptions = []
reuters_timestamps = []
reuters_pages =list(range(1,20))

# loop over reuters news
for page in reuters_pages:
	# send request and extract html
	scrape_params.update({'page': str(page)})
	r = requests.get(url, params=scrape_params)
	print(r)
	html_doc = r.text
	soup = BeautifulSoup(html_doc, 'lxml')

	#get specific content
	reuters_titles = reuters_titles + html_extractor(soup, '.col-10 .story-title')
	reuters_descriptions = reuters_descriptions + html_extractor(soup,'.col-10 p')
	reuters_timestamps = reuters_timestamps + html_extractor(soup, '.timestamp')

# dont convert date into date type! keep them as str for the moment¨(seriously!)
reuters_timestamps =['/str/' + str(time)+ '/str/'for time in reuters_timestamps]

#define url and parameters for scraping BI
url = 'https://www.businessinsider.com/clusterstock'
scrape_params = {
	'IR': 'T',
	'page': ''
}
# define lists for storing data
business_titles = []
business_authors = []
business_timestamps = []
# omit first page due to different formatting
business_pages = list(range(2,21))
# loop over all pages of BI
for page in business_pages:
	# send request and extract html
	scrape_params.update({'page': str(page)})
	r = requests.get(url, params=scrape_params)
	print(r)
	html_doc = r.text
	soup = BeautifulSoup(html_doc, 'lxml')

	#get specific content
	business_titles = business_titles + html_extractor(soup, '.river-post h3')
	business_authors = business_authors + html_extractor(soup, '.ks-author-byline')
	business_timestamps = business_timestamps + html_extractor(soup, '.river-post__date')

# define url and parameters to scrape cnbc.com
url = 'https://www.cnbc.com/business/'
scrape_params = {
    "page": ""
}
cnbc_titles = []
cnbc_snippets = []
cnbc_timestamps = []

# could go further, but should be enough articles
cnbc_pages = list(range(1,20))
for page in cnbc_pages:
	scrape_params.update({"page": str(page)})

	# send request and extract html
	r = requests.get(url, params = scrape_params)
	print(r)
	html_doc = r.text
	soup = BeautifulSoup(html_doc, 'lxml')
	# check if all elements are same length (sometimes snippet is missing)
	# if check fails, skip specific page
	html_titles = html_extractor(soup, '#pipeline_assetlist_0 .headline')
	html_snippets = html_extractor(soup, '#pipeline_assetlist_0 .desc')
	html_timestamps = html_extractor(soup, '#pipeline_assetlist_0 time')

	if len(html_titles) == len(html_snippets) == len(html_timestamps):
		cnbc_titles = cnbc_titles + html_titles
		cnbc_snippets = cnbc_snippets + html_snippets
		cnbc_timestamps = cnbc_timestamps + html_timestamps

# process output
reuters_df = pd.DataFrame(
    {'title': reuters_titles,
     'description': reuters_descriptions,
     'timestamp': reuters_timestamps,
	 'source': 'Reuters',
	 'scrape_date': datetime.today().strftime('%Y-%m-%d')
    })

business_df = pd.DataFrame(
	{'title': business_titles,
	 'source': business_authors,
	 'timestamp': business_timestamps,
	 'scrape_date': datetime.today().strftime('%Y-%m-%d')
	})

cnbc_df = pd.DataFrame(
	{'title': cnbc_titles,
	 'description': cnbc_snippets,
	 'source': 'cnbc',
	 'timestamp': cnbc_timestamps,
	 'scrape_date': datetime.today().strftime('%Y-%m-%d')
	 })

df_list = [reuters_df, business_df, cnbc_df]
# check data
print(business_df.head())
print(reuters_df.head())
print(cnbc_df.head())

# define output file name and paths
file_name =  'scraped_articles.json'
file_paths = [os.path.join(dir_path,'Data/News/Reuters/'),
			  os.path.join(dir_path,'Data/News/BI/'),
			  os.path.join(dir_path, 'Data/News/cnbc/')
			  ]
# server directories:
# file_paths = ['/root/text_mining/news_scraping/Reuters',
# 			  '/root/text_mining/news_scraping/BI',
# 			  '/root/text_mining/news_scraping/cnbc']

file_paths = [os.path.join(path,file_name) for path in file_paths]

# append new data to existing df and remove duplicates, write all dataframes to file
counter = 0
for path in file_paths:
	if(os.path.isfile(path)==True):
		old_df = pd.read_json(path, orient='split')
		df_list[counter] = pd.concat([old_df,df_list[counter]]).drop_duplicates(subset='title').reset_index(drop=True)
	df_list[counter].to_json(path, orient='split')
	counter += 1