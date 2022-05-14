import requests

from bs4 import BeautifulSoup, SoupStrainer


from scraping_utils import html_extractor

# scrape google new
# scrape reuters
# scrape forbes
# scrape some swiss news
# scrape some european news


class NewsScraper:
    def __init__(self, search_query):
        self.query = search_query

    def _query_retuers_news(self):
        url = "https://www.reuters.com/search/news"
        url_params = {
            "blob": self.query,
            "sortBy": "date",
            "dateRange": "pastMonth"
        }
        return requests.get(url, params=url_params)

    @staticmethod
    def _get_news_links(response):
        urls = []
        for link in BeautifulSoup(
            response.text,
            'html.parser',
            parse_only=SoupStrainer('a')
        ):
            if link.has_attr('href'):
                urls.append(link)
        return urls

    def scrape_news(self):
        # make sure that self.query is in the actual text
        reponse = self._query_retuers_news()
        #return self._get_news_links(reponse)


