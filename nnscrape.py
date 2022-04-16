from bs4 import BeautifulSoup
import requests
import pickle
from pathlib import Path


COOKIES_FILE = "cookies.txt"
NN_BASE_URL = "https://www.rit.edu/fa/diningservices/netnutrition/1"
# https://www.rit.edu/fa/diningservices/netnutrition/1/NutritionDetail/ShowItemNutritionLabel

session = requests.Session() 
if Path(COOKIES_FILE).exists():
	with open(COOKIES_FILE, 'rb') as c:
		# contents = c.read()
		# if len(contents) > 0:
		session.cookies.update(pickle.load(c))

homepage = session.get(NN_BASE_URL)

with open(COOKIES_FILE, 'wb') as c:
	pickle.dump(session.cookies, c)

home_html = BeautifulSoup(homepage.content, 'html.parser') 
