from bs4 import BeautifulSoup
import requests_cache
import pickle
from pathlib import Path
from netnutrition import DiningLocation, DiningMenu

COOKIES_FILE = "cookies.txt"
NN_BASE_URL = "https://www.rit.edu/fa/diningservices/netnutrition/1"
# https://www.rit.edu/fa/diningservices/netnutrition/1/NutritionDetail/ShowItemNutritionLabel

session = requests_cache.CachedSession('nn_pagecache')
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
