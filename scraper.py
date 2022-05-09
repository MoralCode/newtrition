from bs4 import BeautifulSoup
import requests
from pathlib import Path

class Scraper:
	"""class that can scrape pages with caching and assist with parsing them
	"""

	def __init__(self, session=None, cachedir=None):
		self._session = session
		# self.cachedir

	def clearcache(self):
		pass

	def _get_client(self):
		if self._session:
			return self._session
		else:
			return requests

	def _find_cache_for(self, method, url):
		pass

	def get(self, url):

		page = self._get_client().get(url)

		# save page in cache?

		return page
