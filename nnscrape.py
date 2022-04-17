from bs4 import BeautifulSoup
import requests_cache
import pickle
from pathlib import Path
from netnutrition import DiningLocation, DiningMenu
from constants import NN_BASE_URL, COOKIES_FILE


# this will need to be put back once this goes live as every POST request needs to hit NN to work
session = requests_cache.CachedSession('nn_pagecache')#, allowable_methods=['GET'])
if Path(COOKIES_FILE).exists():
	with open(COOKIES_FILE, 'rb') as c:
		# contents = c.read()
		# if len(contents) > 0:
		session.cookies.update(pickle.load(c))

homepage = session.get(NN_BASE_URL)

with open(COOKIES_FILE, 'wb') as c:
	pickle.dump(session.cookies, c)

home_html = BeautifulSoup(homepage.content, 'html.parser') 

dining_locations_html = home_html.find(id="cbo_nn_unitDataList").find(class_="row").children
dining_locations = [DiningLocation.from_html(loc) for loc in dining_locations_html]
