import requests
import pandas as pd
from datetime import datetime
import os

dir_path = os.getcwd()
# Define api url and parameters
url =  'https://www.alphavantage.co/query'
symbols = ['WM']
index_quotes = []
query_params = {
	'function': 'SECTOR',
	#'symbol': '',
	'apikey': ''
}

# get sector performance
index_performance = requests.get(url, params=query_params).json()
print(index_performance)

index_performance.pop('Meta Data', None)
for key in index_performance:
	print(index_performance[key])
#write df to file
performance_df = pd.DataFrame.from_dict(index_performance)
performance_df['date'] = datetime.today().strftime('%Y-%m-%d')
performance_df.reset_index(level=0, inplace=True)
performance_df.rename(columns={'index': 'sector'}, inplace=True)
data_path = os.path.join(dir_path, 'Data/S_P_500/s_p_500_perf.csv')
# server path = /root/text_mining/s_p_500/s_p_500_perf.csv
if(os.path.isfile(data_path)==True):
	performance_df.to_csv(data_path, mode='a', header=False)
else:
	performance_df.to_csv(data_path, mode='w', header=True)