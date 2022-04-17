from bs4 import BeautifulSoup
import requests
import requests_cache
import pickle
from pathlib import Path
from netnutrition import DiningLocation, DiningMenu
from constants import NN_BASE_URL, COOKIES_FILE
from helpers import goback
import csv
import argparse


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('mode', choices=['test', 'csv', 'archive'],
                    help='pick a mode')
parser.add_argument('--cached', action='store_true',
                    help='whether caching should be used')
parser.add_argument('--show-cookies', action='store_true',
                    help='whether to print the session id in the cookies')
args = parser.parse_args()


# this will need to be put back once this goes live as every POST request needs to hit NN to work
session = None
if args.cached:
	session=requests_cache.CachedSession('nn_pagecache')
else:
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

if args.show_cookies:
# Get cookies
	print(session.cookies.get_dict())


if args.mode == "csv":
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

elif args.mode == "test":
	dining_locations_html = home_html.find(id="cbo_nn_unitDataList").find(class_="row").children
	dining_locations = [DiningLocation.from_html(loc) for loc in dining_locations_html]


	artesanos = dining_locations[1]
	a_menu = artesanos.get_menus(session = session)[0]
	an_item = a_menu.get_items(session = session)[0]
	print(an_item)
	print(an_item.get_nutrition_info(session=session))

