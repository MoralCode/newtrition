from bs4 import BeautifulSoup
import requests
import pickle
from pathlib import Path
from netnutrition import DiningLocation, DiningMenu
from constants import NN_BASE_URL, COOKIES_FILE
from helpers import goback
import csv

# this will need to be put back once this goes live as every POST request needs to hit NN to work
session = session = requests.Session() #, allowable_methods=['GET'])
if Path(COOKIES_FILE).exists():
	with open(COOKIES_FILE, 'rb') as c:
		# contents = c.read()
		# if len(contents) > 0:
		session.cookies.update(pickle.load(c))

homepage = session.get(NN_BASE_URL)

with open(COOKIES_FILE, 'wb') as c:
	pickle.dump(session.cookies, c)

home_html = BeautifulSoup(homepage.content, 'html.parser') 
item_ids = set()


with open('data.csv', 'w') as csvfile:
	spamwriter = csv.writer(csvfile)
	dining_locations_html = home_html.find(id="cbo_nn_unitDataList").find(class_="row").children
	dining_locations = [DiningLocation.from_html(loc) for loc in dining_locations_html]

	for location in dining_locations:
		menus = location.get_menus(session = session)
		for menu in menus:

			items = menu.get_items(session = session)
			for item in items:
				print("processing loc: {}, menu: {}, item: {}".format(location.identifier, menu.identifier, item.identifier))
				if len(set([item.identifier]).intersection(item_ids)) == 1:
					print("\trepeat item found")
				else:
					item_ids.add(item.identifier)
				nut = item.get_nutrition_info(session=session)
				try:
					spamwriter.writerow([item.name, location.name, nut.serving.calsperserving])
				except Exception as e:
					print("not enough data to write: " + str(e))
			# reset state for the next menu
			goback(session=session)
		# reset state for the next location
		goback(session=session)

