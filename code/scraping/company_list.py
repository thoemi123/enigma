# company list for keyword definition
# Datum: 03.11.2018
# Letzes Update: 30.12.2018
# quellen: 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

# load html_doc or send request again to Wikipedia?
# Warning: if request is sent again, code may not work, since the structure of the specific html has changed over
# the course of this semester (HS 2018).
load_html = True

# import modules
from bs4 import BeautifulSoup
import requests
import os
import pandas as pd
import sys


def scrape_company_list(url, file_name, dir_path):

	# send request
	if load_html == False:
		con = ''
		# wait for user input
		while con != 'yes' and con != 'no':
			con = input('setting load_html = False will override old html file. Do you want to proceed? [yes/no] ')
		if con == 'yes':
			r = requests.get(url)
			html_doc = r.text
			with open(os.path.join(dir_path, file_name), mode='wt', encoding='utf-8') as file:
				file.write(html_doc)
		else:
			sys.exit('Script has stopped due to user input')
	else:
		with open(os.path.join(dir_path, file_name), mode = "rt", encoding='utf-8') as file:
			html_doc = file.read()
	return html_doc


def process_list(html_doc):
	# process html and extract table with s&p500 list
	soup = BeautifulSoup(html_doc, 'lxml')
	table = soup.find('table')


	# get table elements
	rows = table.find_all('tr')
	print(len(rows))
	table_text = []
	for row in table.find_all('tr'):
		cols = row.find_all('td')
		col_text = []
		for col in cols:
			col_text.append(col.get_text())
		table_text.append(col_text)
	print(table_text)
	# add  table header
	header = ['symbol', 'security', 'sec_filing', 'gics_sector', 'sub_industry',
					'location', 'added', 'cik', 'founded']

	# create pandas df for further use
	df = pd.DataFrame(table_text, columns= header)
	return df[['symbol', 'security', 'gics_sector']]

def main():
	dir_path = os.getcwd()
	url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
	html_file = 'Data/Companies/html_doc.txt'
	html_doc = scrape_company_list, dir_path(url, html_file)
	df_out = process_list(html_doc)
	xlsx_path = os.path.join(dir_path, 'Data/Companies/s_p_500_list_raw.xlsx')
	df_out.to_excel(xlsx_path)

if __name__  == "__main__":
	main()

